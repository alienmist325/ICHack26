import styled from "styled-components";
import { FiChevronLeft, FiChevronRight } from "react-icons/fi";
import { rightMoveBlue } from "../../constants";

const PaginationContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem 1rem;
`;

const ResultsInfo = styled.p`
  font-size: 0.9rem;
  color: #666;
  margin: 0;
`;

const PaginationControls = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
`;

const NavButton = styled.button<{ disabled?: boolean }>`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border: 2px solid ${rightMoveBlue};
  background-color: white;
  color: ${rightMoveBlue};
  border-radius: 50%;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;

  &:hover:not(:disabled) {
    background-color: ${rightMoveBlue};
    color: white;
    transform: scale(1.05);
  }

  &:active:not(:disabled) {
    transform: scale(0.95);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
`;

const PageDots = styled.div`
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
  justify-content: center;
`;

const PageDot = styled.button<{ isActive: boolean }>`
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  border: none;
  background-color: ${(props) => (props.isActive ? rightMoveBlue : "#ccc")};
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background-color: ${(props) => (props.isActive ? rightMoveBlue : "#999")};
    transform: scale(1.2);
  }
`;

const EllipsisContainer = styled.span`
  color: #999;
  font-weight: bold;
`;

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  isLoading: boolean;
  onPageChange: (page: number) => void;
}

export const Pagination = ({
  currentPage,
  totalPages,
  totalCount,
  pageSize,
  isLoading,
  onPageChange,
}: PaginationProps) => {
  const startItem = currentPage * pageSize + 1;
  const endItem = Math.min((currentPage + 1) * pageSize, totalCount);

  const handlePreviousPage = () => {
    if (currentPage > 0) {
      onPageChange(currentPage - 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages - 1) {
      onPageChange(currentPage + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const getPageDots = () => {
    const dots = [];
    const maxDotsToShow = 7;

    if (totalPages <= maxDotsToShow) {
      // Show all dots
      for (let i = 0; i < totalPages; i++) {
        dots.push(
          <PageDot
            key={i}
            isActive={i === currentPage}
            onClick={() => {
              onPageChange(i);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            disabled={isLoading}
          />
        );
      }
    } else {
      // Show first, ellipsis, current-1, current, current+1, ellipsis, last
      // First page
      dots.push(
        <PageDot
          key={0}
          isActive={0 === currentPage}
          onClick={() => {
            onPageChange(0);
            window.scrollTo({ top: 0, behavior: "smooth" });
          }}
          disabled={isLoading}
        />
      );

      // Ellipsis or pages before current
      if (currentPage > 2) {
        dots.push(<EllipsisContainer key="ellipsis1">•••</EllipsisContainer>);
      } else if (currentPage === 2) {
        dots.push(
          <PageDot
            key={1}
            isActive={1 === currentPage}
            onClick={() => {
              onPageChange(1);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            disabled={isLoading}
          />
        );
      }

      // Current page and surrounding
      const startPage = Math.max(1, currentPage - 1);
      const endPage = Math.min(totalPages - 2, currentPage + 1);

      for (let i = startPage; i <= endPage; i++) {
        dots.push(
          <PageDot
            key={i}
            isActive={i === currentPage}
            onClick={() => {
              onPageChange(i);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            disabled={isLoading}
          />
        );
      }

      // Ellipsis or pages after current
      if (currentPage < totalPages - 3) {
        dots.push(<EllipsisContainer key="ellipsis2">•••</EllipsisContainer>);
      } else if (currentPage === totalPages - 3) {
        dots.push(
          <PageDot
            key={totalPages - 2}
            isActive={totalPages - 2 === currentPage}
            onClick={() => {
              onPageChange(totalPages - 2);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            disabled={isLoading}
          />
        );
      }

      // Last page
      dots.push(
        <PageDot
          key={totalPages - 1}
          isActive={totalPages - 1 === currentPage}
          onClick={() => {
            onPageChange(totalPages - 1);
            window.scrollTo({ top: 0, behavior: "smooth" });
          }}
          disabled={isLoading}
        />
      );
    }

    return dots;
  };

  if (totalPages <= 1) {
    return null;
  }

  return (
    <PaginationContainer>
      <ResultsInfo>
        Showing {startItem}-{endItem} of {totalCount} properties
      </ResultsInfo>

      <PaginationControls>
        <NavButton
          onClick={handlePreviousPage}
          disabled={currentPage === 0 || isLoading}
          title="Previous page"
        >
          <FiChevronLeft size={20} />
        </NavButton>

        <PageDots>{getPageDots()}</PageDots>

        <NavButton
          onClick={handleNextPage}
          disabled={currentPage === totalPages - 1 || isLoading}
          title="Next page"
        >
          <FiChevronRight size={20} />
        </NavButton>
      </PaginationControls>
    </PaginationContainer>
  );
};
