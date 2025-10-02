/**
 * MealCard Component
 * Feature: 003-update-logic-for
 * Task: T049
 *
 * Expandable meal card with:
 * - Thumbnail preview (replaces apple icon)
 * - Inline expansion on tap
 * - Photo carousel for multi-photo meals
 * - Macronutrient display in grams
 * - Edit and delete actions
 */

import React, { useState } from 'react';
import PhotoCarousel from './PhotoCarousel';

interface Macronutrients {
  protein: number;
  carbs: number;
  fats: number;
}

interface Photo {
  id: string;
  thumbnailUrl: string;
  fullUrl: string;
  displayOrder: number;
}

interface Meal {
  id: string;
  userId: string;
  createdAt: string;
  description: string | null;
  calories: number;
  macronutrients: Macronutrients;
  photos: Photo[];
  confidenceScore: number | null;
}

interface MealCardProps {
  meal: Meal;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  onEdit?: (meal: Meal) => void;
  onDelete?: (mealId: string) => void;
  className?: string;
}

export const MealCard: React.FC<MealCardProps> = ({
  meal,
  isExpanded = false,
  onToggleExpand,
  onEdit,
  onDelete,
  className = '',
}) => {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const hasPhotos = meal.photos && meal.photos.length > 0;
  const thumbnailUrl = hasPhotos ? meal.photos[0].thumbnailUrl : null;

  // Format time
  const time = new Date(meal.createdAt).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });

  const handleThumbnailClick = () => {
    if (onToggleExpand) {
      onToggleExpand();
    }
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onEdit) {
      onEdit(meal);
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDeleteDialog(true);
  };

  const handleConfirmDelete = () => {
    if (onDelete) {
      onDelete(meal.id);
    }
    setShowDeleteDialog(false);
  };

  const handleCancelDelete = () => {
    setShowDeleteDialog(false);
  };

  return (
    <div className={`meal-card ${isExpanded ? 'expanded' : ''} ${className}`}>
      {/* Collapsed View - Always Visible */}
      <div className="meal-card-header" onClick={handleThumbnailClick}>
        <div className="meal-thumbnail">
          {thumbnailUrl ? (
            <img src={thumbnailUrl} alt="Meal" className="thumbnail-image" />
          ) : (
            <div className="placeholder-icon">🍎</div>
          )}
          {meal.photos.length > 1 && (
            <span className="photo-count-badge">{meal.photos.length}</span>
          )}
        </div>

        <div className="meal-summary">
          <div className="meal-time">{time}</div>
          <div className="meal-description">
            {meal.description || 'No description'}
          </div>
          <div className="meal-calories">{Math.round(meal.calories)} kcal</div>
        </div>

        <div className="expand-indicator">
          {isExpanded ? '▼' : '▶'}
        </div>
      </div>

      {/* Expanded View - Shows on Tap */}
      {isExpanded && (
        <div className="meal-card-details">
          {/* Photo Carousel */}
          {hasPhotos && (
            <div className="meal-photos">
              <PhotoCarousel photos={meal.photos} alt={meal.description || 'Meal'} />
            </div>
          )}

          {/* Macronutrients */}
          <div className="macronutrients">
            <h4>🏋️ Macronutrients</h4>
            <div className="macro-grid">
              <div className="macro-item">
                <span className="macro-label">Protein</span>
                <span className="macro-value">{meal.macronutrients.protein.toFixed(1)}g</span>
              </div>
              <div className="macro-item">
                <span className="macro-label">Carbs</span>
                <span className="macro-value">{meal.macronutrients.carbs.toFixed(1)}g</span>
              </div>
              <div className="macro-item">
                <span className="macro-label">Fats</span>
                <span className="macro-value">{meal.macronutrients.fats.toFixed(1)}g</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="meal-actions">
            {onEdit && (
              <button onClick={handleEdit} className="action-button edit-button">
                ✏️ Edit
              </button>
            )}
            {onDelete && (
              <button onClick={handleDelete} className="action-button delete-button">
                🗑️ Delete
              </button>
            )}
          </div>
        </div>
      )}

      <style>{`
        .meal-card {
          background: var(--tg-theme-bg-color, white);
          border-radius: 12px;
          margin-bottom: 12px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          overflow: hidden;
          transition: all 0.3s ease;
        }

        .meal-card.expanded {
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
        }

        .meal-card-header {
          display: flex;
          align-items: center;
          padding: 12px;
          cursor: pointer;
          user-select: none;
        }

        .meal-card-header:active {
          background: var(--tg-theme-secondary-bg-color, #f5f5f5);
        }

        .meal-thumbnail {
          position: relative;
          width: 60px;
          height: 60px;
          border-radius: 8px;
          overflow: hidden;
          flex-shrink: 0;
          margin-right: 12px;
          background: var(--tg-theme-secondary-bg-color, #f5f5f5);
        }

        .thumbnail-image {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .placeholder-icon {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 32px;
        }

        .photo-count-badge {
          position: absolute;
          top: 4px;
          right: 4px;
          background: rgba(0, 0, 0, 0.7);
          color: white;
          border-radius: 10px;
          padding: 2px 6px;
          font-size: 11px;
          font-weight: bold;
        }

        .meal-summary {
          flex: 1;
          min-width: 0;
        }

        .meal-time {
          font-size: 12px;
          color: var(--tg-theme-hint-color, #999);
          margin-bottom: 4px;
        }

        .meal-description {
          font-size: 14px;
          font-weight: 500;
          color: var(--tg-theme-text-color, #000);
          margin-bottom: 4px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .meal-calories {
          font-size: 16px;
          font-weight: bold;
          color: var(--tg-theme-button-color, #007aff);
        }

        .expand-indicator {
          font-size: 12px;
          color: var(--tg-theme-hint-color, #999);
          margin-left: 8px;
        }

        .meal-card-details {
          padding: 0 12px 12px 12px;
          animation: expandAnimation 0.3s ease;
        }

        @keyframes expandAnimation {
          from {
            opacity: 0;
            max-height: 0;
          }
          to {
            opacity: 1;
            max-height: 1000px;
          }
        }

        .meal-photos {
          margin-bottom: 16px;
        }

        .macronutrients {
          margin-bottom: 16px;
          padding: 12px;
          background: var(--tg-theme-secondary-bg-color, #f5f5f5);
          border-radius: 8px;
        }

        .macronutrients h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          color: var(--tg-theme-text-color, #000);
        }

        .macro-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
        }

        .macro-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
        }

        .macro-label {
          font-size: 11px;
          color: var(--tg-theme-hint-color, #999);
          margin-bottom: 4px;
          text-transform: uppercase;
        }

        .macro-value {
          font-size: 16px;
          font-weight: bold;
          color: var(--tg-theme-text-color, #000);
        }

        .meal-actions {
          display: flex;
          gap: 8px;
        }

        .action-button {
          flex: 1;
          padding: 10px;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: opacity 0.2s;
          min-height: 44px;
        }

        .action-button:active {
          opacity: 0.7;
        }

        .edit-button {
          background: var(--tg-theme-button-color, #007aff);
          color: var(--tg-theme-button-text-color, white);
        }

        .delete-button {
          background: #ff3b30;
          color: white;
        }

        .no-photos-placeholder {
          padding: 40px;
          text-align: center;
          color: var(--tg-theme-hint-color, #999);
          background: var(--tg-theme-secondary-bg-color, #f5f5f5);
          border-radius: 8px;
          font-size: 32px;
        }

        .confirmation-dialog {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .confirmation-dialog-content {
          background: var(--tg-theme-bg-color, white);
          border-radius: 16px;
          padding: 24px;
          max-width: 400px;
          width: 90%;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }

        .confirmation-dialog h3 {
          margin: 0 0 16px 0;
          font-size: 18px;
          color: var(--tg-theme-text-color, #000);
        }

        .confirmation-dialog p {
          margin: 0 0 24px 0;
          color: var(--tg-theme-hint-color, #666);
        }

        .confirmation-dialog-buttons {
          display: flex;
          gap: 12px;
          justify-content: flex-end;
        }

        .confirmation-dialog button {
          padding: 8px 16px;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
        }

        .confirmation-dialog .cancel-button {
          background: var(--tg-theme-secondary-bg-color, #f5f5f5);
          color: var(--tg-theme-text-color, #000);
        }

        .confirmation-dialog .confirm-button {
          background: #ff4444;
          color: white;
        }
      `}</style>

      {/* Confirmation Dialog */}
      {showDeleteDialog && (
        <div className="confirmation-dialog" onClick={handleCancelDelete}>
          <div className="confirmation-dialog-content" onClick={(e) => e.stopPropagation()}>
            <h3>Delete Meal</h3>
            <p>Are you sure you want to delete this meal?</p>
            <div className="confirmation-dialog-buttons">
              <button className="cancel-button" onClick={handleCancelDelete}>
                Cancel
              </button>
              <button className="confirm-button" onClick={handleConfirmDelete}>
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MealCard;
