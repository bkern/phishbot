import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryInput } from './QueryInput'

test('renders the textarea', () => {
  render(<QueryInput onSubmit={vi.fn()} disabled={false} />)
  expect(screen.getByPlaceholderText(/ask anything about phish/i)).toBeInTheDocument()
})

test('renders the Ask button', () => {
  render(<QueryInput onSubmit={vi.fn()} disabled={false} />)
  expect(screen.getByRole('button', { name: /ask/i })).toBeInTheDocument()
})

test('renders the three example chips', () => {
  render(<QueryInput onSubmit={vi.fn()} disabled={false} />)
  expect(screen.getByText('longest Tweezer?')).toBeInTheDocument()
  expect(screen.getByText('Maze in first set 2024')).toBeInTheDocument()
  expect(screen.getByText('Carini stats')).toBeInTheDocument()
})

test('calls onSubmit with typed question when Ask clicked', async () => {
  const onSubmit = vi.fn()
  render(<QueryInput onSubmit={onSubmit} disabled={false} />)
  await userEvent.type(screen.getByRole('textbox'), 'longest Tweezer?')
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))
  expect(onSubmit).toHaveBeenCalledWith('longest Tweezer?')
})

test('clicking a chip populates the textarea', () => {
  render(<QueryInput onSubmit={vi.fn()} disabled={false} />)
  fireEvent.click(screen.getByText('Carini stats'))
  expect(screen.getByRole('textbox')).toHaveValue('Carini stats')
})

test('does not call onSubmit when question is empty', () => {
  const onSubmit = vi.fn()
  render(<QueryInput onSubmit={onSubmit} disabled={false} />)
  fireEvent.click(screen.getByRole('button', { name: /ask/i }))
  expect(onSubmit).not.toHaveBeenCalled()
})

test('Ask button is disabled when disabled prop is true', () => {
  render(<QueryInput onSubmit={vi.fn()} disabled={true} />)
  expect(screen.getByRole('button', { name: /ask/i })).toBeDisabled()
})
