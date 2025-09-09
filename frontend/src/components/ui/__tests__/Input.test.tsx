import { describe, it, expect } from 'vitest';
import { render, screen } from '../../../test/utils/test-utils';
import Input from '../Input';

describe('Input', () => {
  it('renders input with placeholder', () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
  });

  it('shows error state', () => {
    render(<Input error="This field is required" />);
    expect(screen.getByText('This field is required')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveClass('border-red-500');
  });

  it('renders with left icon', () => {
    const TestIcon = () => <span data-testid="test-icon">Icon</span>;
    render(<Input leftIcon={<TestIcon />} placeholder="With icon" />);

    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('With icon')).toBeInTheDocument();
  });

  it('renders with right icon', () => {
    const TestIcon = () => <span data-testid="test-icon">Icon</span>;
    render(<Input rightIcon={<TestIcon />} placeholder="With icon" />);

    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
  });

  it('applies different sizes correctly', () => {
    const { rerender } = render(<Input size="sm" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveClass('px-3', 'py-2');

    rerender(<Input size="lg" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveClass('px-4', 'py-3');
  });

  it('handles disabled state', () => {
    render(<Input disabled placeholder="Disabled input" />);
    expect(screen.getByPlaceholderText('Disabled input')).toBeDisabled();
  });
});
