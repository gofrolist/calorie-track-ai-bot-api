import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PhotoCarousel } from "../PhotoCarousel";
import type { MealPhotoInfo } from "@/api/model";

const mockPhotos: MealPhotoInfo[] = [
  {
    id: "p1",
    thumbnailUrl: "thumb1.jpg",
    fullUrl: "full1.jpg",
    displayOrder: 0,
  },
  {
    id: "p2",
    thumbnailUrl: "thumb2.jpg",
    fullUrl: "full2.jpg",
    displayOrder: 1,
  },
];

describe("PhotoCarousel", () => {
  it("renders photos", () => {
    const { container } = render(<PhotoCarousel photos={mockPhotos} />);
    const images = container.querySelectorAll("img");
    expect(images).toHaveLength(2);
  });

  it("renders nothing when no photos", () => {
    const { container } = render(<PhotoCarousel photos={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
