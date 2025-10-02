/**
 * MealEditor Component
 * Feature: 003-update-logic-for
 * Task: T050
 *
 * Modal for editing meal details:
 * - Description
 * - Macronutrients (protein, carbs, fats in grams)
 * - Auto-calculates calories from macros
 */

import React, { useState, useEffect } from 'react';

interface Macronutrients {
  protein: number;
  carbs: number;
  fats: number;
}

interface Meal {
  id: string;
  description: string | null;
  calories: number;
  macronutrients: Macronutrients;
}

interface MealEditorProps {
  meal: Meal;
  isOpen: boolean;
  onClose: () => void;
  onSave: (updates: MealUpdate) => Promise<void>;
}

interface MealUpdate {
  description?: string;
  protein_grams?: number;
  carbs_grams?: number;
  fats_grams?: number;
}

export const MealEditor: React.FC<MealEditorProps> = ({
  meal,
  isOpen,
  onClose,
  onSave,
}) => {
  const [description, setDescription] = useState(meal.description || '');
  const [protein, setProtein] = useState(meal.macronutrients.protein.toString());
  const [carbs, setCarbs] = useState(meal.macronutrients.carbs.toString());
  const [fats, setFats] = useState(meal.macronutrients.fats.toString());
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // Reset form when meal changes
  useEffect(() => {
    setDescription(meal.description || '');
    setProtein(meal.macronutrients.protein.toFixed(1));
    setCarbs(meal.macronutrients.carbs.toFixed(1));
    setFats(meal.macronutrients.fats.toFixed(1));
  }, [meal]);

  // Handle keyboard events
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  // Calculate estimated calories (4-4-9 formula)
  const estimatedCalories = Math.round(
    (parseFloat(protein) || 0) * 4 +
    (parseFloat(carbs) || 0) * 4 +
    (parseFloat(fats) || 0) * 9
  );

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    setValidationErrors([]);

    try {
      // Validate inputs
      const errors: string[] = [];
      const newProtein = parseFloat(protein);
      const newCarbs = parseFloat(carbs);
      const newFats = parseFloat(fats);

      if (newProtein < 0 || newCarbs < 0 || newFats < 0) {
        errors.push('Macronutrients must be positive');
      }

      if (errors.length > 0) {
        setValidationErrors(errors);
        setIsSaving(false);
        return;
      }

      const updates: MealUpdate = {};

      if (description !== meal.description) {
        updates.description = description || undefined;
      }

      if (newProtein !== meal.macronutrients.protein) {
        updates.protein_grams = newProtein;
      }
      if (newCarbs !== meal.macronutrients.carbs) {
        updates.carbs_grams = newCarbs;
      }
      if (newFats !== meal.macronutrients.fats) {
        updates.fats_grams = newFats;
      }

      await onSave(updates);
      onClose();
    } catch (error) {
      console.error('Error saving meal:', error);
      setError('Failed to update meal');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    // Reset to original values
    setDescription(meal.description || '');
    setProtein(meal.macronutrients.protein.toString());
    setCarbs(meal.macronutrients.carbs.toString());
    setFats(meal.macronutrients.fats.toString());
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="meal-editor-overlay" onClick={onClose}>
      <div className="meal-editor-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Edit Meal</h2>
          <button onClick={onClose} className="close-button">
            ✕
          </button>
        </div>

        <div className="modal-content">
          {/* Error Messages */}
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {validationErrors.length > 0 && (
            <div className="validation-error">
              {validationErrors.map((error, index) => (
                <div key={index}>{error}</div>
              ))}
            </div>
          )}

          {/* Description */}
          <div className="form-group">
            <label htmlFor="description">Description</label>
            <input
              id="description"
              name="description"
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Grilled chicken pasta"
              maxLength={1000}
              className="form-input"
            />
          </div>

          {/* Macronutrients */}
          <div className="form-group">
            <label>Macronutrients (grams)</label>
            <div className="macro-inputs">
              <div className="macro-input-group">
                <label htmlFor="protein" className="macro-input-label">Protein</label>
                <input
                  id="protein"
                  name="protein_grams"
                  type="number"
                  value={protein}
                  onChange={(e) => setProtein(e.target.value)}
                  min="0"
                  step="0.1"
                  className="form-input-small"
                />
                <span className="unit">g</span>
              </div>

              <div className="macro-input-group">
                <label htmlFor="carbs" className="macro-input-label">Carbs</label>
                <input
                  id="carbs"
                  name="carbs_grams"
                  type="number"
                  value={carbs}
                  onChange={(e) => setCarbs(e.target.value)}
                  min="0"
                  step="0.1"
                  className="form-input-small"
                />
                <span className="unit">g</span>
              </div>

              <div className="macro-input-group">
                <label htmlFor="fats" className="macro-input-label">Fats</label>
                <input
                  id="fats"
                  name="fats_grams"
                  type="number"
                  value={fats}
                  onChange={(e) => setFats(e.target.value)}
                  min="0"
                  step="0.1"
                  className="form-input-small"
                />
                <span className="unit">g</span>
              </div>
            </div>
          </div>

          {/* Estimated Calories */}
          <div className="calories-preview">
            <span className="calories-label">Estimated Calories:</span>
            <span className="calories-value">{estimatedCalories} kcal</span>
          </div>

          {/* Extra content for mobile scrolling test */}
          <div className="extra-content">
            <p>Additional content to ensure scrolling works on mobile devices.</p>
            <p>This helps test the responsive design and scrolling behavior.</p>
            <p>More content to make the modal taller.</p>
            <p>Even more content to ensure scrolling is triggered.</p>
            <p>Final paragraph to guarantee sufficient height.</p>
          </div>
        </div>

        <div className="modal-actions">
          <button
            onClick={handleCancel}
            disabled={isSaving}
            className="button-secondary cancel-button"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="button-primary save-button"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>

        <style>{`
          .meal-editor-overlay {
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
            padding: 16px;
          }

          .meal-editor-modal {
            background: var(--tg-theme-bg-color, white);
            border-radius: 16px;
            max-width: 500px;
            width: 100%;
            max-height: 60vh;
            overflow-y: auto;
            overflow-x: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
          }

          .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px;
            border-bottom: 1px solid var(--tg-theme-secondary-bg-color, #eee);
          }

          .modal-header h2,
          .modal-header h3 {
            margin: 0;
            font-size: 18px;
            color: var(--tg-theme-text-color, #000);
          }

          .close-button {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: var(--tg-theme-hint-color, #999);
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
          }

          .modal-content {
            padding: 16px;
          }

          .error-message {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            border: 1px solid #fcc;
          }

          .validation-error {
            background: #fef3cd;
            color: #856404;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            border: 1px solid #ffeaa7;
          }

          .form-group {
            margin-bottom: 20px;
          }

          .form-group label {
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
            font-weight: 500;
            color: var(--tg-theme-text-color, #000);
          }

          .form-input {
            width: 100%;
            padding: 12px;
            border: 1px solid var(--tg-theme-secondary-bg-color, #ddd);
            border-radius: 8px;
            font-size: 16px;
            background: var(--tg-theme-bg-color, white);
            color: var(--tg-theme-text-color, #000);
          }

          .macro-inputs {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
          }

          .macro-input-group {
            display: flex;
            flex-direction: column;
            align-items: center;
          }

          .macro-input-label {
            font-size: 12px;
            color: var(--tg-theme-hint-color, #999);
            margin-bottom: 4px;
          }

          .form-input-small {
            width: 100%;
            padding: 8px;
            border: 1px solid var(--tg-theme-secondary-bg-color, #ddd);
            border-radius: 8px;
            font-size: 16px;
            text-align: center;
            background: var(--tg-theme-bg-color, white);
            color: var(--tg-theme-text-color, #000);
          }

          .unit {
            font-size: 12px;
            color: var(--tg-theme-hint-color, #999);
            margin-top: 4px;
          }

          .calories-preview {
            padding: 12px;
            background: var(--tg-theme-button-color, #007aff);
            color: var(--tg-theme-button-text-color, white);
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 500;
          }

          .calories-label {
            font-size: 14px;
          }

          .calories-value {
            font-size: 18px;
            font-weight: bold;
          }

          .extra-content {
            margin-top: 20px;
            padding: 16px;
            background: var(--tg-theme-secondary-bg-color, #f5f5f5);
            border-radius: 8px;
          }

          .extra-content p {
            margin: 8px 0;
            font-size: 14px;
            color: var(--tg-theme-hint-color, #999);
          }

          .modal-actions {
            display: flex;
            gap: 12px;
            padding: 16px;
            border-top: 1px solid var(--tg-theme-secondary-bg-color, #eee);
          }

          .button-secondary,
          .button-primary {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            min-height: 44px;
            transition: opacity 0.2s;
          }

          .button-secondary {
            background: var(--tg-theme-secondary-bg-color, #f5f5f5);
            color: var(--tg-theme-text-color, #000);
          }

          .button-primary {
            background: var(--tg-theme-button-color, #007aff);
            color: var(--tg-theme-button-text-color, white);
          }

          .button-primary:disabled,
          .button-secondary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }

          .button-primary:active:not(:disabled),
          .button-secondary:active:not(:disabled) {
            opacity: 0.8;
          }
        `}</style>
      </div>
    </div>
  );
};

export default MealEditor;
