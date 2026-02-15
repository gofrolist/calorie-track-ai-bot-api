import type { MealPhotoInfo } from '@/api/model';

interface PhotoCarouselProps {
  photos: MealPhotoInfo[];
}

export function PhotoCarousel({ photos }: PhotoCarouselProps) {
  if (photos.length === 0) return null;

  if (photos.length === 1) {
    return (
      <img
        src={photos[0].fullUrl}
        alt=""
        className="w-full rounded-xl object-cover"
      />
    );
  }

  return (
    <div className="flex gap-2 overflow-x-auto pb-2">
      {photos
        .sort((a, b) => a.displayOrder - b.displayOrder)
        .map((photo) => (
          <img
            key={photo.id}
            src={photo.fullUrl}
            alt=""
            className="h-48 w-48 shrink-0 rounded-xl object-cover"
          />
        ))}
    </div>
  );
}
