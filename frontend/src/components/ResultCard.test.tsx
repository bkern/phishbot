import { render, screen } from '@testing-library/react'
import { ResultCard } from './ResultCard'

test('renders answer text when not loading', () => {
  render(
    <ResultCard
      question="What opened most in 2024?"
      answer="Sigma Oasis opened 7 shows."
      sources={['setlist.fm']}
      loading={false}
    />
  )
  expect(screen.getByText('Sigma Oasis opened 7 shows.')).toBeInTheDocument()
})

test('echoes the question in the header', () => {
  render(
    <ResultCard
      question="What opened most in 2024?"
      answer="Sigma Oasis opened 7 shows."
      sources={['setlist.fm']}
      loading={false}
    />
  )
  expect(screen.getByText('"What opened most in 2024?"')).toBeInTheDocument()
})

test('renders source tags', () => {
  render(
    <ResultCard
      question="test"
      answer="answer"
      sources={['setlist.fm', 'phish.net']}
      loading={false}
    />
  )
  expect(screen.getByText('setlist.fm')).toBeInTheDocument()
  expect(screen.getByText('phish.net')).toBeInTheDocument()
})

test('shows Thinking label when loading', () => {
  render(
    <ResultCard question="test" answer="" sources={[]} loading={true} />
  )
  expect(screen.getByText('Thinking...')).toBeInTheDocument()
})

test('hides ANSWER label when loading', () => {
  render(
    <ResultCard question="test" answer="" sources={[]} loading={true} />
  )
  expect(screen.queryByText('ANSWER')).not.toBeInTheDocument()
})

test('shows ANSWER label when not loading', () => {
  render(
    <ResultCard question="test" answer="some answer" sources={[]} loading={false} />
  )
  expect(screen.getByText('ANSWER')).toBeInTheDocument()
})
