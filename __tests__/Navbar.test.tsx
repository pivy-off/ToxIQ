import { render, screen, fireEvent } from '@testing-library/react';
import Navbar from '@/components/Navbar';

describe('Navbar', () => {
  const mockOnPageChange = jest.fn();

  beforeEach(() => {
    mockOnPageChange.mockClear();
  });

  it('renders the logo', () => {
    render(
      <Navbar currentPage="input" onPageChange={mockOnPageChange} hasResults={false} />
    );
    expect(screen.getByText('ToxIQ')).toBeInTheDocument();
  });

  it('renders navigation links', () => {
    render(
      <Navbar currentPage="input" onPageChange={mockOnPageChange} hasResults={true} />
    );
    expect(screen.getByText('Simulator')).toBeInTheDocument();
    expect(screen.getByText('Safety Score')).toBeInTheDocument();
    expect(screen.getByText('Scientific Details')).toBeInTheDocument();
  });

  it('marks current page as active', () => {
    render(
      <Navbar currentPage="results" onPageChange={mockOnPageChange} hasResults={true} />
    );
    const safetyLink = screen.getByText('Safety Score');
    expect(safetyLink).toHaveClass('nav-active');
  });

  it('disables results links when no results', () => {
    render(
      <Navbar currentPage="input" onPageChange={mockOnPageChange} hasResults={false} />
    );
    const safetyLink = screen.getByText('Safety Score');
    expect(safetyLink).toHaveClass('nav-disabled');
  });

  it('calls onPageChange when logo is clicked', () => {
    render(
      <Navbar currentPage="results" onPageChange={mockOnPageChange} hasResults={true} />
    );
    fireEvent.click(screen.getByText('ToxIQ'));
    expect(mockOnPageChange).toHaveBeenCalledWith('input');
  });

  it('calls onPageChange when nav link is clicked', () => {
    render(
      <Navbar currentPage="input" onPageChange={mockOnPageChange} hasResults={true} />
    );
    fireEvent.click(screen.getByText('Safety Score'));
    expect(mockOnPageChange).toHaveBeenCalledWith('results');
  });
});
