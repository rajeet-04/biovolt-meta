import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { ExperimentForm } from '../../src/components/experiments/ExperimentForm'

it('requires a complete arm before submit', async () => {
  const submit = vi.fn()
  const user = userEvent.setup()
  render(<ExperimentForm onSubmit={submit} />)
  await user.click(screen.getByRole('button', { name: 'Create experiment' }))
  expect(screen.getByRole('alert')).toHaveTextContent('Name, device, cell')
  expect(submit).not.toHaveBeenCalled()
})

it('collects exact passive arm setpoints', async () => {
  const submit = vi.fn()
  const user = userEvent.setup()
  render(<ExperimentForm onSubmit={submit} />)
  await user.type(screen.getByLabelText('Name'), 'Run A')
  await user.type(screen.getByLabelText('Device 1'), 'biovolt-01')
  await user.type(screen.getByLabelText('Cell 1'), 'cell-a')
  await user.click(screen.getByRole('button', { name: 'Create experiment' }))
  expect(submit).toHaveBeenCalledWith(expect.objectContaining({ name: 'Run A', arms: [expect.objectContaining({ device_id: 'biovolt-01', cell_id: 'cell-a', mode: 'passive' })] }))
})
