// src/components/common/__tests__/ControlButton.test.tsx — Tests for ControlButton
import { describe, it, expect, vi } from 'vitest';
import { render, userEvent } from '../../../test/utils';
import ControlButton from '../ControlButton';

describe('ControlButton', () => {
  it('should render children', () => {
    const { container } = render(
      <ControlButton onClick={() => {}}>Click me</ControlButton>
    );
    expect(container.textContent).toContain('Click me');
  });

  it('should call onClick when clicked', async () => {
    const onClick = vi.fn();
    const { getByRole } = render(
      <ControlButton onClick={onClick}>Click me</ControlButton>
    );
    await userEvent.click(getByRole('button'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('should not call onClick when disabled', async () => {
    const onClick = vi.fn();
    const { getByRole } = render(
      <ControlButton onClick={onClick} disabled>Click me</ControlButton>
    );
    await userEvent.click(getByRole('button'));
    expect(onClick).not.toHaveBeenCalled();
  });

  it('should not call onClick when loading', async () => {
    const onClick = vi.fn();
    const { getByRole } = render(
      <ControlButton onClick={onClick} loading>Click me</ControlButton>
    );
    await userEvent.click(getByRole('button'));
    expect(onClick).not.toHaveBeenCalled();
  });

  it('should render loading spinner', () => {
    const { container } = render(
      <ControlButton onClick={() => {}} loading>Click me</ControlButton>
    );
    expect(container.textContent).toContain('⏳');
  });

  it('should render icon', () => {
    const { container } = render(
      <ControlButton onClick={() => {}} icon={<span>🚀</span>}>Click me</ControlButton>
    );
    expect(container.textContent).toContain('🚀');
  });

  it('should apply primary variant', () => {
    const { getByRole } = render(
      <ControlButton onClick={() => {}} variant="primary">Click me</ControlButton>
    );
    expect(getByRole('button')).toHaveClass('bg-blue-600');
  });

  it('should apply danger variant', () => {
    const { getByRole } = render(
      <ControlButton onClick={() => {}} variant="danger">Click me</ControlButton>
    );
    expect(getByRole('button')).toHaveClass('bg-red-600');
  });

  it('should apply success variant', () => {
    const { getByRole } = render(
      <ControlButton onClick={() => {}} variant="success">Click me</ControlButton>
    );
    expect(getByRole('button')).toHaveClass('bg-green-600');
  });

  it('should apply small size', () => {
    const { getByRole } = render(
      <ControlButton onClick={() => {}} size="sm">Click me</ControlButton>
    );
    expect(getByRole('button')).toHaveClass('text-xs');
  });

  it('should apply medium size', () => {
    const { getByRole } = render(
      <ControlButton onClick={() => {}} size="md">Click me</ControlButton>
    );
    expect(getByRole('button')).toHaveClass('text-sm');
  });

  it('should apply large size', () => {
    const { getByRole } = render(
      <ControlButton onClick={() => {}} size="lg">Click me</ControlButton>
    );
    expect(getByRole('button')).toHaveClass('text-base');
  });

  it('should apply custom className', () => {
    const { getByRole } = render(
      <ControlButton onClick={() => {}} className="custom-class">Click me</ControlButton>
    );
    expect(getByRole('button')).toHaveClass('custom-class');
  });

  it('should apply title', () => {
    const { getByRole } = render(
      <ControlButton onClick={() => {}} title="Button title">Click me</ControlButton>
    );
    expect(getByRole('button')).toHaveAttribute('title', 'Button title');
  });
});
