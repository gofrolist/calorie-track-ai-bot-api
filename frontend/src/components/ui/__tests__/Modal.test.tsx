import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Modal } from '../Modal';

describe('Modal', () => {
  it('renders children when open', () => {
    render(
      <Modal open onClose={() => {}}>
        <p>content</p>
      </Modal>,
    );
    expect(screen.getByText('content')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <Modal open={false} onClose={() => {}}>
        <p>content</p>
      </Modal>,
    );
    expect(screen.queryByText('content')).not.toBeInTheDocument();
  });

  it('calls onClose when backdrop clicked', async () => {
    const onClose = vi.fn();
    render(
      <Modal open onClose={onClose}>
        <p>content</p>
      </Modal>,
    );
    await userEvent.click(screen.getByTestId('modal-backdrop'));
    expect(onClose).toHaveBeenCalled();
  });

  it('has correct aria attributes', () => {
    render(
      <Modal open onClose={() => {}} title="Test">
        <p>content</p>
      </Modal>,
    );
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-label', 'Test');
  });
});
