import { useState, useEffect } from "react";
import styled from "styled-components";
import { House } from "../../types";
import { Button } from "./Button";
import { rightMoveBlue } from "../../constants";
import { api } from "../../api/client";

import { IoBed } from "react-icons/io5";
import { GiHouse } from "react-icons/gi";
import { FaMoneyBillAlt } from "react-icons/fa";
import { FaToiletPaper } from "react-icons/fa6";
import { FiChevronLeft, FiChevronRight, FiStar, FiMessageCircle } from "react-icons/fi";
import { AiOutlineLike, AiOutlineDislike, AiFillLike, AiFillDislike } from "react-icons/ai";
import { FiHome, FiBox } from "react-icons/fi";
import { BsStarFill } from "react-icons/bs";

export interface HouseCardProps {
  house: House;
}

const CardContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: #f9f9f9;
  }
`;

const ImageContainer = styled.div`
  position: relative;
  width: 250px;
  height: 200px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  background-color: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const Image = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: opacity 0.3s ease;
`;

const PlaceholderIcon = styled.div`
  font-size: 4rem;
  color: rgba(240, 80, 40, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
`;

const CarouselControls = styled.div<{ visible: boolean }>`
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

const ArrowButton = styled.button`
  background: rgba(255, 255, 255, 0.8);
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s ease;

  &:hover {
    background: white;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const ImageCounter = styled.div`
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
  color: #212529;
`;

const InfoRow = styled.p`
  margin: 0.25rem 0;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #555;
`;

const Features = styled.ul`
  margin: 0.5rem 0 0 0;
  padding-left: 1.2rem;
  font-size: 0.85rem;
  color: #666;
`;

const RatingContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #eee;
`;

const RatingButton = styled.button<{ isActive: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.8rem;
  border: 2px solid ${(props) => (props.isActive ? rightMoveBlue : "#ccc")};
  background: ${(props) => (props.isActive ? rightMoveBlue : "white")};
  color: ${(props) => (props.isActive ? "white" : "#666")};
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s ease;

  &:hover {
    border-color: ${rightMoveBlue};
    background: ${(props) => (props.isActive ? rightMoveBlue : "white")};
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
  color: #666;
  margin-left: 0.5rem;
`;

const ActionBar = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
  flex-wrap: wrap;
`;

const StarButton = styled.button<{ isBookmarked: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.8rem;
  border: 2px solid ${(props) => (props.isBookmarked ? "#FFD700" : "#ccc")};
  background: ${(props) => (props.isBookmarked ? "#fffbf0" : "white")};
  color: ${(props) => (props.isBookmarked ? "#FFD700" : "#666")};
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s ease;

  &:hover {
    border-color: #FFD700;
    background: #fffbf0;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const StatusSelect = styled.select`
  padding: 0.4rem 0.8rem;
  border: 2px solid #ccc;
  border-radius: 20px;
  background: white;
  color: #666;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: ${rightMoveBlue};
  }

  &:focus {
    outline: none;
    border-color: ${rightMoveBlue};
    box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const CommentsSection = styled.div`
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
`;

const CommentsButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.8rem;
  border: 2px solid #ccc;
  background: white;
  color: #666;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s ease;

  &:hover {
    border-color: ${rightMoveBlue};
    color: ${rightMoveBlue};
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const CommentCount = styled.span`
  font-size: 0.8rem;
  color: #999;
  margin-left: 0.3rem;
`;

type PropertyStatus = "interested" | "viewing" | "offer" | "accepted" | null;

export function HouseCard(props: HouseCardProps) {
  const { house } = props;
  const [isHovering, setIsHovering] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [autoPlayInterval, setAutoPlayInterval] = useState<NodeJS.Timeout | null>(null);
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
      }, 3000);
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
      if (typeof window !== 'undefined' && window.__toastContext) {
        const message = voteType === "upvote" ? "⭐ Starred this property!" : "❌ Marked as gone from market!";
        window.__toastContext.addToast(message, "success", 2000);
      }
    } catch (err) {
      console.error("Failed to vote:", err);
      if (typeof window !== 'undefined' && window.__toastContext) {
        window.__toastContext.addToast("Failed to record rating", "error", 3000);
      }
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
        if (typeof window !== 'undefined' && window.__toastContext) {
          window.__toastContext.addToast("Removed from bookmarks", "success", 2000);
        }
      } else {
        await api.starProperty(house.id);
        setIsBookmarked(true);
        if (typeof window !== 'undefined' && window.__toastContext) {
          window.__toastContext.addToast("Added to bookmarks", "success", 2000);
        }
      }
    } catch (err) {
      console.error("Failed to bookmark:", err);
      if (typeof window !== 'undefined' && window.__toastContext) {
        window.__toastContext.addToast("Failed to update bookmark", "error", 3000);
      }
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
      if (typeof window !== 'undefined' && window.__toastContext) {
        const statusText = status ? `Status updated to "${status}"` : "Status cleared";
        window.__toastContext.addToast(statusText, "success", 2000);
      }
    } catch (err) {
      console.error("Failed to update status:", err);
      if (typeof window !== 'undefined' && window.__toastContext) {
        window.__toastContext.addToast("Failed to update status", "error", 3000);
      }
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
                <FiChevronLeft size={20} />
              </ArrowButton>
              <ArrowButton onClick={handleNextImage}>
                <FiChevronRight size={20} />
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
          <GiHouse /> <strong>Address:</strong> {house.full_address || house.address}
        </InfoRow>

        <InfoRow>
          <FaMoneyBillAlt /> <strong>Price:</strong> £{house.price.toLocaleString()}
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

         <RatingContainer>
           <RatingButton
             isActive={userVote === "upvote"}
             onClick={() => handleVote("upvote")}
             disabled={isVoting}
             title="Star this property"
           >
             {userVote === "upvote" ? <AiFillLike size={16} /> : <AiOutlineLike size={16} />}
             <span>Star</span>
           </RatingButton>

           <RatingButton
             isActive={userVote === "downvote"}
             onClick={() => handleVote("downvote")}
             disabled={isVoting}
             title="Mark as gone from market"
           >
             {userVote === "downvote" ? <AiFillDislike size={16} /> : <AiOutlineDislike size={16} />}
             <span>Gone</span>
           </RatingButton>

           {house.score !== undefined && (
             <ScoreDisplay>
               Score: {house.score.toFixed(1)}
             </ScoreDisplay>
           )}
         </RatingContainer>

         <ActionBar>
           <StarButton
             isBookmarked={isBookmarked}
             onClick={handleToggleBookmark}
             disabled={isVoting}
             title="Add to bookmarks"
           >
             {isBookmarked ? <BsStarFill size={16} /> : <FiStar size={16} />}
             <span>{isBookmarked ? "Bookmarked" : "Bookmark"}</span>
           </StarButton>

           <StatusSelect
             value={propertyStatus || ""}
             onChange={(e) => handleStatusChange((e.target.value as PropertyStatus) || null)}
             disabled={isUpdatingStatus}
             title="Track your property status"
           >
             <option value="">Set Status...</option>
             <option value="interested">Interested</option>
             <option value="viewing">Viewing Scheduled</option>
             <option value="offer">Made Offer</option>
             <option value="accepted">Offer Accepted</option>
           </StatusSelect>

           <CommentsButton
             onClick={() => setShowComments(!showComments)}
             title="View and add comments"
           >
             <FiMessageCircle size={16} />
             <span>Comments</span>
             <CommentCount>({commentCount})</CommentCount>
           </CommentsButton>
         </ActionBar>

         {showComments && (
           <CommentsSection>
             <p style={{ color: "#999", fontSize: "0.9rem" }}>
               Comments feature coming soon! This property has {commentCount} comments.
             </p>
           </CommentsSection>
         )}
       </ContentContainer>
     </CardContainer>
   );
 }
