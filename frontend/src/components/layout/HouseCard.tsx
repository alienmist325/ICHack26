import { useState, useEffect } from "react";
import styled from "styled-components";
import { House } from "../../types";
import { Button } from "./Button";
import { colors } from "../../constants";
import { api } from "../../api/client";
import { useToast } from "../hooks/useToast";
import { useNavigate } from "react-router-dom";

import { IoBed } from "react-icons/io5";
import { GiHouse } from "react-icons/gi";
import { FaMoneyBillAlt } from "react-icons/fa";
import { FaToiletPaper } from "react-icons/fa6";
import {
  FiChevronLeft,
  FiChevronRight,
  FiStar,
  FiMessageCircle,
} from "react-icons/fi";
import {
  AiOutlineLike,
  AiOutlineDislike,
  AiFillLike,
  AiFillDislike,
} from "react-icons/ai";
import { FiHome, FiBox } from "react-icons/fi";
import { BsStarFill } from "react-icons/bs";

export interface HouseCardProps {
  house: House;
}

export const CardContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 1.5rem;
  border-bottom: 1px solid ${colors.borderColor};
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  background-color: ${colors.white};
  position: relative;
  border-left: 4px solid transparent;

  &:hover {
    background-color: ${colors.lightBg};
    transform: translateX(4px);
    border-left-color: ${colors.teal};
    box-shadow:
      inset 0 0 0 1px ${colors.borderColor},
      0 4px 16px ${colors.teal}10;
  }
`;

const ImageContainer = styled.div`
  position: relative;
  width: 250px;
  height: 200px;
  flex-shrink: 0;
  border-radius: 12px;
  overflow: hidden;
  background-color: ${colors.lightBg};
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.02);
    box-shadow: 0 8px 24px rgba(73, 223, 181, 0.15);
  }
`;

const Image = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: opacity 0.3s ease;
`;

export const PlaceholderIcon = styled.div`
  font-size: 4rem;
  color: ${colors.teal}40;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pulse 2s ease-in-out infinite;

  @keyframes pulse {
    0%,
    100% {
      opacity: 0.6;
    }
    50% {
      opacity: 1;
    }
  }
`;

export const CarouselControls = styled.div<{ visible: boolean }>`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;
  opacity: ${(props) => (props.visible ? 1 : 0)};
  transition: opacity 0.2s ease;
  background: rgba(0, 0, 0, 0.2);
`;

export const ArrowButton = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;

  background: rgba(255, 255, 255, 0.8);
  width: 40px;
  height: 32px;
  justify-content: center;
  transition: background 0.2s ease;

  &:hover {
    background: white;
  }

  &:disabled {
    opacity: 0.1;
    cursor: not-allowed;
  }
`;

export const LargeChevronRight = styled(FiChevronRight)`
  transform: scale(2);
  transform-origin: center;
`;

export const LargeChevronLeft = styled(FiChevronLeft)`
  transform: scale(2);
  transform-origin: center;
`;

export const ImageCounter = styled.div`
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
`;

const ContentContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const Title = styled.h2`
  margin: 0;
  font-size: 1.3rem;
  color: ${colors.darkText};
`;

const InfoRow = styled.p`
  margin: 0.25rem 0;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: ${colors.medText};
`;

const Features = styled.ul`
  margin: 0.5rem 0 0 0;
  padding-left: 1.2rem;
  font-size: 0.85rem;
  color: ${colors.lightText};
`;

const RatingContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid ${colors.borderColor};
`;

const RatingButton = styled.button<{ isActive: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.8rem;
  border: 2px solid
    ${(props) => (props.isActive ? colors.teal : colors.borderColor)};
  background: ${(props) => (props.isActive ? colors.teal : colors.white)};
  color: ${(props) => (props.isActive ? colors.white : colors.medText)};
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.3s ease;

  &:hover {
    border-color: ${colors.teal};
    background: ${(props) => (props.isActive ? colors.teal : colors.lightBg)};
    transform: translateY(-2px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:active {
    transform: scale(0.95);
  }
`;

const ScoreDisplay = styled.span`
  font-size: 0.85rem;
  color: ${colors.lightText};
  margin-left: 0.5rem;
`;

const ActionBar = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid ${colors.borderColor};
  flex-wrap: wrap;
`;

const StarButton = styled.button<{ isBookmarked: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.8rem;
  border: 2px solid
    ${(props) => (props.isBookmarked ? colors.teal : colors.borderColor)};
  background: ${(props) =>
    props.isBookmarked ? `${colors.teal}15` : colors.white};
  color: ${(props) => (props.isBookmarked ? colors.teal : colors.medText)};
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.3s ease;

  &:hover {
    border-color: ${colors.teal};
    background: ${`${colors.teal}15`};
    transform: translateY(-2px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const StatusSelect = styled.select`
  padding: 0.4rem 0.8rem;
  border: 2px solid ${colors.borderColor};
  border-radius: 20px;
  background: ${colors.white};
  color: ${colors.medText};
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    border-color: ${colors.teal};
  }

  &:focus {
    outline: none;
    border-color: ${colors.teal};
    box-shadow: 0 0 0 2px ${colors.teal}20;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const CommentsSection = styled.div`
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid ${colors.borderColor};
`;

const CommentsButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.8rem;
  border: 2px solid ${colors.borderColor};
  background: ${colors.white};
  color: ${colors.medText};
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.3s ease;

  &:hover {
    border-color: ${colors.teal};
    color: ${colors.teal};
    transform: translateY(-2px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const CommentCount = styled.span`
  font-size: 0.8rem;
  color: ${colors.lightText};
  margin-left: 0.3rem;
`;

type PropertyStatus = "interested" | "viewing" | "offer" | "accepted" | null;

export function HouseCard(props: HouseCardProps) {
  const { house } = props;
  const { addToast } = useToast();
  const [isHovering, setIsHovering] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [autoPlayInterval, setAutoPlayInterval] =
    useState<NodeJS.Timeout | null>(null);
  const [userVote, setUserVote] = useState<"upvote" | "downvote" | null>(null);
  const [isVoting, setIsVoting] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [propertyStatus, setPropertyStatus] = useState<PropertyStatus>(null);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [commentCount, setCommentCount] = useState(0);
  const [showComments, setShowComments] = useState(false);

  const images = house.images && house.images.length > 0 ? house.images : [];
  const hasImages = images.length > 0;

  // Auto-cycle images on hover
  useEffect(() => {
    if (isHovering && hasImages) {
      const interval = setInterval(() => {
        setCurrentImageIndex((prev) => (prev + 1) % images.length);
      }, 1000);
      setAutoPlayInterval(interval);
    } else {
      if (autoPlayInterval) {
        clearInterval(autoPlayInterval);
        setAutoPlayInterval(null);
      }
      setCurrentImageIndex(0);
    }

    return () => {
      if (autoPlayInterval) {
        clearInterval(autoPlayInterval);
      }
    };
  }, [isHovering, hasImages, images.length]);

  const handlePreviousImage = () => {
    setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
    if (autoPlayInterval) {
      clearInterval(autoPlayInterval);
      setAutoPlayInterval(null);
    }
  };

  const handleNextImage = () => {
    setCurrentImageIndex((prev) => (prev + 1) % images.length);
    if (autoPlayInterval) {
      clearInterval(autoPlayInterval);
      setAutoPlayInterval(null);
    }
  };

  const handleVote = async (voteType: "upvote" | "downvote") => {
    setIsVoting(true);
    try {
      await api.postRating(house.id, voteType);
      setUserVote(voteType);

      // Show toast notification
      const message =
        voteType === "upvote"
          ? "⭐ Starred this property!"
          : "❌ Marked as gone from market!";
      addToast(message, "success", 2000);
    } catch (err) {
      console.error("Failed to vote:", err);
      addToast("Failed to record rating", "error", 3000);
    } finally {
      setIsVoting(false);
    }
  };

  const handleToggleBookmark = async () => {
    setIsVoting(true);
    try {
      if (isBookmarked) {
        await api.unstarProperty(house.id);
        setIsBookmarked(false);
        addToast("Removed from bookmarks", "success", 2000);
      } else {
        await api.starProperty(house.id);
        setIsBookmarked(true);
        addToast("Added to bookmarks", "success", 2000);
      }
    } catch (err) {
      console.error("Failed to bookmark:", err);
      addToast("Failed to update bookmark", "error", 3000);
    } finally {
      setIsVoting(false);
    }
  };

  const handleStatusChange = async (status: PropertyStatus) => {
    setIsUpdatingStatus(true);
    try {
      if (status) {
        await api.setPropertyStatus(house.id, status);
      }
      setPropertyStatus(status);
      const statusText = status
        ? `Status updated to "${status}"`
        : "Status cleared";
      addToast(statusText, "success", 2000);
    } catch (err) {
      console.error("Failed to update status:", err);
      addToast("Failed to update status", "error", 3000);
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const getPropertyIcon = () => {
    const type = house.property_type?.toLowerCase() || "";
    if (type.includes("flat") || type.includes("apartment")) {
      return <FiBox />;
    }
    return <FiHome />;
  };

  const navigate = useNavigate();

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  return (
    <CardContainer>
      <ImageContainer
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => setIsHovering(false)}
      >
        {hasImages ? (
          <>
            <Image
              src={images[currentImageIndex]}
              alt={`${house.listingTitle} - Image ${currentImageIndex + 1}`}
            />
            <CarouselControls visible={isHovering}>
              <ArrowButton onClick={handlePreviousImage}>
                <LargeChevronLeft />
              </ArrowButton>
              <ArrowButton onClick={handleNextImage}>
                <LargeChevronRight />
              </ArrowButton>
            </CarouselControls>
            {isHovering && (
              <ImageCounter>
                {currentImageIndex + 1}/{images.length}
              </ImageCounter>
            )}
          </>
        ) : (
          <PlaceholderIcon>{getPropertyIcon()}</PlaceholderIcon>
        )}
      </ImageContainer>

      <ContentContainer>
        <Title>{house.listingTitle}</Title>

        <InfoRow>
          <GiHouse /> <strong>Address:</strong>{" "}
          {house.full_address || house.address}
          <div> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; </div>
          <FaMoneyBillAlt /> <strong>Price:</strong> £
          {house.price.toLocaleString()}
        </InfoRow>

        <InfoRow>
          <FaMoneyBillAlt /> <strong>Price:</strong> £
          {house.price.toLocaleString()}
        </InfoRow>

        {house.bedrooms !== undefined && (
          <InfoRow>
            <IoBed /> <strong>Bedrooms:</strong> {house.bedrooms}
          </InfoRow>
        )}

        {house.bathrooms !== undefined && (
          <InfoRow>
            <FaToiletPaper /> <strong>Bathrooms:</strong> {house.bathrooms}
          </InfoRow>
        )}

        {house.features && house.features.length > 0 && (
          <Features>
            {house.features.map((feature, index) => (
              <li key={index}>{feature}</li>
            ))}
          </Features>
        )}
        <Button
          onClick={() => handleNavigation(`/house/${house.id}`)}
          style={{ color: "#000000ff", backgroundColor: "#49dfb5" }}
        >
          View more details
        </Button>

        <RatingContainer>
          <RatingButton
            isActive={userVote === "upvote"}
            onClick={() => handleVote("upvote")}
            disabled={isVoting}
            title="Star this property"
          >
            {userVote === "upvote" ? (
              <AiFillLike size={16} />
            ) : (
              <AiOutlineLike size={16} />
            )}
            <span>Star</span>
          </RatingButton>

          <RatingButton
            isActive={userVote === "downvote"}
            onClick={() => handleVote("downvote")}
            disabled={isVoting}
            title="Mark as gone from market"
          >
            {userVote === "downvote" ? (
              <AiFillDislike size={16} />
            ) : (
              <AiOutlineDislike size={16} />
            )}
            <span>Gone</span>
          </RatingButton>

          {house.score !== undefined && (
            <ScoreDisplay>Score: {house.score.toFixed(1)}</ScoreDisplay>
          )}
        </RatingContainer>
      </ContentContainer>
    </CardContainer>
  );
}
