import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { mealsApi, type Meal } from '../services/api';
import { TelegramWebAppContext } from '../app';

interface EditFormData {
  kcal_total: number;
  macros: {
    protein_g: number;
    fat_g: number;
    carbs_g: number;
  };
}

interface ValidationErrors {
  kcal_total?: string;
  protein_g?: string;
  fat_g?: string;
  carbs_g?: string;
}

export const MealDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const telegramContext = useContext(TelegramWebAppContext);

  const [meal, setMeal] = useState<Meal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<EditFormData>({
    kcal_total: 0,
    macros: { protein_g: 0, fat_g: 0, carbs_g: 0 }
  });
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (!id) {
      setError('Meal ID is required');
      setLoading(false);
      return;
    }

    const fetchMeal = async () => {
      try {
        setLoading(true);
        setError(null);
        const mealData = await mealsApi.getMeal(id);
        setMeal(mealData);

        // Initialize edit form with current data
        setEditForm({
          kcal_total: mealData.kcal_total,
          macros: {
            protein_g: mealData.macros?.protein_g || 0,
            fat_g: mealData.macros?.fat_g || 0,
            carbs_g: mealData.macros?.carbs_g || 0,
          }
        });
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('Meal not found');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchMeal();
  }, [id]);

  const getMealTypeLabel = (mealType: string): string => {
    return t(`mealDetail.mealTypes.${mealType}`);
  };

  const getMealTypeIcon = (mealType: string): string => {
    const icons = {
      breakfast: '🌅',
      lunch: '☀️',
      dinner: '🌙',
      snack: '🍎',
    };
    return icons[mealType as keyof typeof icons] || '🍽️';
  };

  const formatMacro = (grams: number | undefined): string => {
    return grams ? `${Math.round(grams)}g` : '0g';
  };

  const validateForm = (): boolean => {
    const errors: ValidationErrors = {};

    if (editForm.kcal_total < 0) {
      errors.kcal_total = 'Calories must be a positive number';
    }

    if (editForm.macros.protein_g < 0 || isNaN(editForm.macros.protein_g)) {
      errors.protein_g = 'Protein must be a valid number';
    }

    if (editForm.macros.fat_g < 0 || isNaN(editForm.macros.fat_g)) {
      errors.fat_g = 'Fat must be a valid number';
    }

    if (editForm.macros.carbs_g < 0 || isNaN(editForm.macros.carbs_g)) {
      errors.carbs_g = 'Carbs must be a valid number';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleEdit = () => {
    setIsEditing(true);
    setValidationErrors({});
    setSaveMessage(null);
  };

  const handleCancel = () => {
    if (!meal) return;

    setIsEditing(false);
    setValidationErrors({});
    setSaveMessage(null);

    // Reset form to original values
    setEditForm({
      kcal_total: meal.kcal_total,
      macros: {
        protein_g: meal.macros?.protein_g || 0,
        fat_g: meal.macros?.fat_g || 0,
        carbs_g: meal.macros?.carbs_g || 0,
      }
    });
  };

  const handleSave = async () => {
    if (!meal || !id) return;

    if (!validateForm()) {
      return;
    }

    try {
      setSaveLoading(true);
      setSaveMessage(null);

      const updatedMeal = await mealsApi.updateMeal(id, {
        kcal_total: editForm.kcal_total,
        macros: editForm.macros,
        corrected: true,
      });

      setMeal(updatedMeal);
      setIsEditing(false);
      setSaveMessage('Meal updated successfully');

      // Clear message after 3 seconds
      setTimeout(() => setSaveMessage(null), 3000);

    } catch (err) {
      console.error('Failed to save meal:', err);
      setSaveMessage('Failed to save changes. Please try again.');
    } finally {
      setSaveLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!meal || !id) return;

    try {
      await mealsApi.deleteMeal(id);
      setSaveMessage('Meal deleted successfully');

      // Navigate back after short delay
      setTimeout(() => {
        navigate('/');
      }, 1500);

    } catch (err) {
      console.error('Failed to delete meal:', err);
      setSaveMessage('Failed to delete meal. Please try again.');
      setShowDeleteConfirm(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    const numValue = parseFloat(value) || 0;

    if (field === 'kcal_total') {
      setEditForm(prev => ({ ...prev, kcal_total: numValue }));
    } else {
      setEditForm(prev => ({
        ...prev,
        macros: { ...prev.macros, [field]: numValue }
      }));
    }

    // Clear validation error for this field
    if (validationErrors[field as keyof ValidationErrors]) {
      setValidationErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }
  };

  if (loading) {
    return (
      <div className="main-content" style={{ padding: 16 }}>
        <div className="loading">Loading meal details...</div>
      </div>
    );
  }

  if (error || !meal) {
    return (
      <div className="main-content" style={{ padding: 16 }}>
        <h1>Meal Detail</h1>
        <div className="error">{error || 'Meal not found'}</div>
        <button className="tg-link" onClick={() => navigate('/')}>
          Back to Today
        </button>
      </div>
    );
  }

  return (
    <div className="main-content" style={{ padding: 16 }}>
      {/* Header */}
      <header style={{ marginBottom: 24 }}>
        <button
          className="tg-link"
          onClick={() => navigate('/')}
          style={{ marginBottom: 16, display: 'block' }}
        >
          ← Back to Today
        </button>
        <h1>Meal Detail</h1>
      </header>

      {/* Save Message */}
      {saveMessage && (
        <div className={`${saveMessage.includes('successfully') ? 'success' : 'error'}`}>
          {saveMessage}
        </div>
      )}

      {/* Meal Photo */}
      {meal.photo_url && (
        <div className="tg-card" style={{ marginBottom: 24, padding: 0, overflow: 'hidden' }}>
          <img
            src={meal.photo_url}
            alt={`Photo of ${getMealTypeLabel(meal.meal_type)}`}
            style={{
              width: '100%',
              height: 250,
              objectFit: 'cover',
              display: 'block'
            }}
          />
        </div>
      )}

      {/* Meal Info Card */}
      <div className="tg-card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          {meal.photo_url ? (
            <div
              style={{
                width: 50,
                height: 50,
                borderRadius: 10,
                backgroundImage: `url(${meal.photo_url})`,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                flexShrink: 0
              }}
            />
          ) : (
            <div style={{ fontSize: '2em' }}>
              {getMealTypeIcon(meal.meal_type)}
            </div>
          )}
          <div>
            <h2 style={{ margin: 0 }}>{getMealTypeLabel(meal.meal_type)}</h2>
            <div style={{ color: 'var(--tg-hint-color)', fontSize: '0.9em' }}>
              {new Date(meal.meal_date).toLocaleDateString(telegramContext.user?.language || 'en', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </div>
          </div>
        </div>

        {/* Calories */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 8, fontWeight: 'bold' }}>
            Calories
          </label>
          {isEditing ? (
            <div>
              <input
                type="number"
                aria-label="Calories"
                value={editForm.kcal_total}
                onChange={(e) => handleInputChange('kcal_total', e.target.value)}
                style={{
                  width: '100%',
                  padding: 12,
                  border: `1px solid ${validationErrors.kcal_total ? '#ff3b30' : 'var(--tg-hint-color)'}`,
                  borderRadius: 8,
                  fontSize: '1em',
                  backgroundColor: 'var(--tg-bg-color)',
                  color: 'var(--tg-text-color)',
                }}
              />
              {validationErrors.kcal_total && (
                <div style={{ color: '#ff3b30', fontSize: '0.9em', marginTop: 4 }}>
                  {validationErrors.kcal_total}
                </div>
              )}
            </div>
          ) : (
            <div style={{ fontSize: '1.2em' }}>
              {meal.kcal_total.toLocaleString()} kcal
            </div>
          )}
        </div>

        {/* Macros */}
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 12 }}>Macronutrients</h3>

          {/* Protein */}
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4 }}>Protein (g)</label>
            {isEditing ? (
              <div>
                <input
                  type="number"
                  aria-label="Protein (g)"
                  value={editForm.macros.protein_g}
                  onChange={(e) => handleInputChange('protein_g', e.target.value)}
                  style={{
                    width: '100%',
                    padding: 8,
                    border: `1px solid ${validationErrors.protein_g ? '#ff3b30' : 'var(--tg-hint-color)'}`,
                    borderRadius: 6,
                    fontSize: '0.9em',
                    backgroundColor: 'var(--tg-bg-color)',
                    color: 'var(--tg-text-color)',
                  }}
                />
                {validationErrors.protein_g && (
                  <div style={{ color: '#ff3b30', fontSize: '0.8em', marginTop: 2 }}>
                    {validationErrors.protein_g}
                  </div>
                )}
              </div>
            ) : (
              <div>{formatMacro(meal.macros?.protein_g)} protein</div>
            )}
          </div>

          {/* Fat */}
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4 }}>Fat (g)</label>
            {isEditing ? (
              <div>
                <input
                  type="number"
                  aria-label="Fat (g)"
                  value={editForm.macros.fat_g}
                  onChange={(e) => handleInputChange('fat_g', e.target.value)}
                  style={{
                    width: '100%',
                    padding: 8,
                    border: `1px solid ${validationErrors.fat_g ? '#ff3b30' : 'var(--tg-hint-color)'}`,
                    borderRadius: 6,
                    fontSize: '0.9em',
                    backgroundColor: 'var(--tg-bg-color)',
                    color: 'var(--tg-text-color)',
                  }}
                />
                {validationErrors.fat_g && (
                  <div style={{ color: '#ff3b30', fontSize: '0.8em', marginTop: 2 }}>
                    {validationErrors.fat_g}
                  </div>
                )}
              </div>
            ) : (
              <div>{formatMacro(meal.macros?.fat_g)} fat</div>
            )}
          </div>

          {/* Carbs */}
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4 }}>Carbs (g)</label>
            {isEditing ? (
              <div>
                <input
                  type="number"
                  aria-label="Carbs (g)"
                  value={editForm.macros.carbs_g}
                  onChange={(e) => handleInputChange('carbs_g', e.target.value)}
                  style={{
                    width: '100%',
                    padding: 8,
                    border: `1px solid ${validationErrors.carbs_g ? '#ff3b30' : 'var(--tg-hint-color)'}`,
                    borderRadius: 6,
                    fontSize: '0.9em',
                    backgroundColor: 'var(--tg-bg-color)',
                    color: 'var(--tg-text-color)',
                  }}
                />
                {validationErrors.carbs_g && (
                  <div style={{ color: '#ff3b30', fontSize: '0.8em', marginTop: 2 }}>
                    {validationErrors.carbs_g}
                  </div>
                )}
              </div>
            ) : (
              <div>{formatMacro(meal.macros?.carbs_g)} carbs</div>
            )}
          </div>
        </div>

        {/* Corrected indicator */}
        {meal.corrected && !isEditing && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            color: 'var(--tg-hint-color)',
            fontSize: '0.9em',
            marginBottom: 16
          }}>
            <span>📝</span>
            <span>Corrected</span>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {isEditing ? (
            <>
              <button
                className="tg-button"
                onClick={handleSave}
                disabled={saveLoading}
                style={{ opacity: saveLoading ? 0.6 : 1 }}
              >
                {saveLoading ? 'Saving...' : 'Save'}
              </button>
              <button
                className="tg-button-secondary"
                onClick={handleCancel}
                disabled={saveLoading}
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button className="tg-button" onClick={handleEdit}>
                Edit
              </button>
              <button
                className="tg-button-secondary"
                onClick={() => setShowDeleteConfirm(true)}
                style={{ backgroundColor: '#ff3b30', color: 'white', border: 'none' }}
              >
                Delete
              </button>
            </>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div className="tg-card" style={{ margin: 16, maxWidth: 400 }}>
            <h3 style={{ marginTop: 0 }}>Delete Meal</h3>
            <p>Are you sure you want to delete this meal?</p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button
                className="tg-button-secondary"
                onClick={() => setShowDeleteConfirm(false)}
              >
                Cancel
              </button>
              <button
                className="tg-button"
                onClick={handleDelete}
                style={{ backgroundColor: '#ff3b30', borderColor: '#ff3b30' }}
              >
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Additional Info */}
      <div className="tg-card">
        <h3 style={{ marginTop: 0 }}>Details</h3>
        <div style={{ display: 'grid', gap: 8, fontSize: '0.9em' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--tg-hint-color)' }}>Created:</span>
            <span>
              {new Date(meal.created_at).toLocaleString(telegramContext.user?.language || 'en')}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--tg-hint-color)' }}>Last Updated:</span>
            <span>
              {new Date(meal.updated_at).toLocaleString(telegramContext.user?.language || 'en')}
            </span>
          </div>
          {meal.estimate_id && (
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--tg-hint-color)' }}>Source:</span>
              <span>AI Estimate</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
