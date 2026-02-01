import styled from "styled-components";
import { Toast, ToastType } from "../hooks/useToast";
import { FiCheckCircle, FiAlertCircle, FiInfo, FiX } from "react-icons/fi";

const ToastContainer = styled.div`
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 400px;
  pointer-events: none;
`;

const ToastItem = styled.div<{ type: ToastType }>`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background-color: white;
  border-left: 4px solid;
  border-left-color: ${(props) => {
    switch (props.type) {
      case "success":
        return "#10b981";
      case "error":
        return "#ef4444";
      case "warning":
        return "#f59e0b";
      case "info":
      default:
        return "#3b82f6";
    }
  }};
  border-radius: 6px;
  box-shadow: ${(props) => {
    switch (props.type) {
      case "success":
        return "0 4px 12px rgba(16, 185, 129, 0.2)";
      case "error":
        return "0 4px 12px rgba(239, 68, 68, 0.2)";
      case "warning":
        return "0 4px 12px rgba(245, 158, 11, 0.2)";
      case "info":
      default:
        return "0 4px 12px rgba(59, 130, 246, 0.2)";
    }
  }};
  animation: slideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  pointer-events: auto;
  max-width: 100%;

  @keyframes slideIn {
    from {
      transform: translateX(400px) scale(0.9);
      opacity: 0;
    }
    to {
      transform: translateX(0) scale(1);
      opacity: 1;
    }
  }
`;

const IconContainer = styled.div<{ type: ToastType }>`
  color: ${(props) => {
    switch (props.type) {
      case "success":
        return "#10b981";
      case "error":
        return "#ef4444";
      case "warning":
        return "#f59e0b";
      case "info":
      default:
        return "#3b82f6";
    }
  }};
  flex-shrink: 0;
  animation: iconBounce 0.6s ease-out;

  @keyframes iconBounce {
    0% {
      transform: scale(0) rotate(-45deg);
      opacity: 0;
    }
    50% {
      transform: scale(1.2) rotate(10deg);
    }
    100% {
      transform: scale(1) rotate(0deg);
      opacity: 1;
    }
  }
`;

const MessageContainer = styled.div`
  flex: 1;
  font-size: 0.9rem;
  color: #333;
  word-break: break-word;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  padding: 0;
  display: flex;
  align-items: center;
  transition: color 0.2s ease;
  flex-shrink: 0;

  &:hover {
    color: #333;
  }
`;

const getIcon = (type: ToastType) => {
  switch (type) {
    case "success":
      return <FiCheckCircle size={20} />;
    case "error":
      return <FiAlertCircle size={20} />;
    case "warning":
      return <FiAlertCircle size={20} />;
    case "info":
    default:
      return <FiInfo size={20} />;
  }
};

interface ToastListProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

export function ToastList({ toasts, onRemove }: ToastListProps) {
  return (
    <ToastContainer>
      {toasts.map((toast) => (
        <ToastItem key={toast.id} type={toast.type}>
          <IconContainer type={toast.type}>{getIcon(toast.type)}</IconContainer>
          <MessageContainer>{toast.message}</MessageContainer>
          <CloseButton onClick={() => onRemove(toast.id)}>
            <FiX size={18} />
          </CloseButton>
        </ToastItem>
      ))}
    </ToastContainer>
  );
}
