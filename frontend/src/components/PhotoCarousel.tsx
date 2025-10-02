/**
 * PhotoCarousel Component
 * Feature: 003-update-logic-for
 * Task: T048
 *
 * Instagram-style photo carousel with:
 * - Swipe gestures for touch devices
 * - Pagination dots at bottom
 * - Navigation arrows on sides
 * - Hides controls for single photos
 * - Keyboard navigation support
 */

import React from 'react';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Navigation, Pagination, Keyboard } from 'swiper/modules';

// Swiper styles
import 'swiper/css';
import 'swiper/css/navigation';
import 'swiper/css/pagination';

interface Photo {
  id: string;
  fullUrl: string;
  thumbnailUrl: string;
  displayOrder: number;
}

interface PhotoCarouselProps {
  photos: Photo[];
  alt?: string;
  className?: string;
}

export const PhotoCarousel: React.FC<PhotoCarouselProps> = ({
  photos,
  alt = 'Meal photo',
  className = '',
}) => {
  // Don't show carousel controls for single photo
  const showControls = photos.length > 1;

  if (photos.length === 0) {
    return (
      <div className="no-photos-placeholder">
        <span>📷 No photos available</span>
      </div>
    );
  }

  // Sort by display order
  const sortedPhotos = [...photos].sort((a, b) => a.displayOrder - b.displayOrder);

  return (
    <div className={`photo-carousel ${className}`}>
      <Swiper
        modules={[Navigation, Pagination, Keyboard]}
        navigation={showControls}
        pagination={{
          clickable: true,
          enabled: showControls,
        }}
        keyboard={{
          enabled: true,
        }}
        loop={false}
        spaceBetween={10}
        slidesPerView={1}
        className="meal-photo-swiper"
        aria-label={`Photo carousel with ${photos.length} photos`}
        role="region"
      >
        {sortedPhotos.map((photo, index) => (
          <SwiperSlide key={photo.id}>
            <div className="photo-slide">
              <img
                src={photo.fullUrl}
                alt={`${alt} ${index + 1}`}
                loading={index === 0 ? 'eager' : 'lazy'}
                className="meal-photo"
              />
            </div>
          </SwiperSlide>
        ))}
      </Swiper>

      <style>{`
        .photo-carousel {
          width: 100%;
          max-width: 100%;
          position: relative;
        }

        .meal-photo-swiper {
          width: 100%;
          height: auto;
          border-radius: 8px;
          overflow: hidden;
        }

        .photo-slide {
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--tg-theme-secondary-bg-color, #f5f5f5);
        }

        .meal-photo {
          width: 100%;
          height: auto;
          max-height: 400px;
          object-fit: contain;
        }

        /* Swiper navigation arrows */
        .swiper-button-next,
        .swiper-button-prev {
          color: var(--tg-theme-button-color, #007aff);
          background: rgba(255, 255, 255, 0.9);
          border-radius: 50%;
          width: 40px;
          height: 40px;
        }

        .swiper-button-next::after,
        .swiper-button-prev::after {
          font-size: 20px;
        }

        /* Pagination dots */
        .swiper-pagination-bullet {
          background: var(--tg-theme-button-color, #007aff);
          opacity: 0.4;
        }

        .swiper-pagination-bullet-active {
          opacity: 1;
        }

        /* Mobile optimizations */
        @media (max-width: 640px) {
          .swiper-button-next,
          .swiper-button-prev {
            width: 36px;
            height: 36px;
          }

          .swiper-button-next::after,
          .swiper-button-prev::after {
            font-size: 18px;
          }
        }

        .no-photos-placeholder {
          padding: 40px;
          text-align: center;
          color: var(--tg-theme-hint-color, #999);
          background: var(--tg-theme-secondary-bg-color, #f5f5f5);
          border-radius: 8px;
        }
      `}</style>
    </div>
  );
};

export default PhotoCarousel;
