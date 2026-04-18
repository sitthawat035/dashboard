// src/components/common/__tests__/StatusBadge.test.tsx — Tests for StatusBadge
import { describe, it, expect } from 'vitest';
import { render } from '../../../test/utils';
import StatusBadge from '../StatusBadge';

describe('StatusBadge', () => {
  it('should render online status', () => {
    const { container } = render(<StatusBadge status="online" />);
    expect(container.textContent).toContain('Online');
  });

  it('should render offline status', () => {
    const { container } = render(<StatusBadge status="offline" />);
    expect(container.textContent).toContain('Offline');
  });

  it('should render starting status', () => {
    const { container } = render(<StatusBadge status="starting" />);
    expect(container.textContent).toContain('Starting');
  });

  it('should render error status', () => {
    const { container } = render(<StatusBadge status="error" />);
    expect(container.textContent).toContain('Error');
  });

  it('should render custom label', () => {
    const { container } = render(<StatusBadge status="online" label="Custom Label" />);
    expect(container.textContent).toContain('Custom Label');
  });

  it('should render with dot by default', () => {
    const { container } = render(<StatusBadge status="online" />);
    // Find the dot span (w-2 h-2 rounded-full)
    const dot = container.querySelector('.w-2.h-2.rounded-full');
    expect(dot).toBeInTheDocument();
  });

  it('should render without dot when showDot is false', () => {
    const { container } = render(<StatusBadge status="online" showDot={false} />);
    // Should not find the dot span
    const dot = container.querySelector('.w-2.h-2.rounded-full');
    expect(dot).not.toBeInTheDocument();
  });

  it('should apply small size', () => {
    const { container } = render(<StatusBadge status="online" size="sm" />);
    const badge = container.querySelector('span');
    expect(badge).toHaveClass('text-xs');
  });

  it('should apply medium size', () => {
    const { container } = render(<StatusBadge status="online" size="md" />);
    const badge = container.querySelector('span');
    expect(badge).toHaveClass('text-sm');
  });

  it('should apply large size', () => {
    const { container } = render(<StatusBadge status="online" size="lg" />);
    const badge = container.querySelector('span');
    expect(badge).toHaveClass('text-base');
  });
});
