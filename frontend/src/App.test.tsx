import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from './App'

function mockFetch(answer: string, sources: string[] = []) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ answer, sources }),
  } as unknown as Response)
}

afterEach(() => {
  vi.restoreAllMocks()
})

test('sends empty history on first question', async () => {
  mockFetch('Tweezer was last played December 31, 2025.')
  render(<App />)

  fireEvent.change(screen.getByRole('textbox'), {
    target: { value: 'when was tweezer last played?' },
  })
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))

  await waitFor(() => {
    const call = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    const body = JSON.parse(call[1].body)
    expect(body.history).toEqual([])
  })
})

test('sends accumulated history on second question', async () => {
  mockFetch('Tweezer was last played December 31, 2025.')
  render(<App />)

  fireEvent.change(screen.getByRole('textbox'), {
    target: { value: 'when was tweezer last played?' },
  })
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))
  await waitFor(() => screen.getByText('ANSWER'))

  mockFetch('Carini was last played recently.')
  fireEvent.change(screen.getByRole('textbox'), {
    target: { value: 'what about carini?' },
  })
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))

  await waitFor(() => {
    const secondCall = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    const body = JSON.parse(secondCall[1].body)
    expect(body.history).toHaveLength(2)
    expect(body.history[0]).toEqual({
      role: 'user',
      content: 'when was tweezer last played?',
    })
    expect(body.history[1]).toEqual({
      role: 'assistant',
      content: 'Tweezer was last played December 31, 2025.',
    })
  })
})

test('new conversation button appears after first answer', async () => {
  mockFetch('Tweezer was last played December 31, 2025.')
  render(<App />)

  expect(screen.queryByText('New Conversation')).not.toBeInTheDocument()

  fireEvent.change(screen.getByRole('textbox'), {
    target: { value: 'when was tweezer last played?' },
  })
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))

  await waitFor(() => screen.getByText('New Conversation'))
})

test('new conversation button resets state', async () => {
  mockFetch('Tweezer was last played December 31, 2025.')
  render(<App />)

  fireEvent.change(screen.getByRole('textbox'), {
    target: { value: 'when was tweezer last played?' },
  })
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))
  await waitFor(() => screen.getByText('New Conversation'))

  fireEvent.click(screen.getByText('New Conversation'))

  expect(screen.queryByText('New Conversation')).not.toBeInTheDocument()
  expect(screen.queryByText('ANSWER')).not.toBeInTheDocument()
})
