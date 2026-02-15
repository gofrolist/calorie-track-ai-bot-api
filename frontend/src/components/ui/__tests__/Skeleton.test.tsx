import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Skeleton } from '../Skeleton';

describe('Skeleton', () => {
  it('renders with aria-busy', () => {
    render(<Skeleton className="h-4 w-32" />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-busy', 'true');
  });
});
