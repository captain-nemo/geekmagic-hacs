import { describe, it, expect } from "vitest";
import { rgbToHex, parseColorInput, type RGBTuple } from "./color-utils";

describe("rgbToHex", () => {
  it("converts basic RGB values to hex", () => {
    expect(rgbToHex([255, 0, 0])).toBe("#ff0000");
    expect(rgbToHex([0, 255, 0])).toBe("#00ff00");
    expect(rgbToHex([0, 0, 255])).toBe("#0000ff");
  });

  it("converts mixed RGB values to hex", () => {
    expect(rgbToHex([255, 128, 0])).toBe("#ff8000");
    expect(rgbToHex([128, 128, 128])).toBe("#808080");
    expect(rgbToHex([255, 255, 255])).toBe("#ffffff");
    expect(rgbToHex([0, 0, 0])).toBe("#000000");
  });

  it("pads single-digit hex values with zeros", () => {
    expect(rgbToHex([1, 2, 3])).toBe("#010203");
    expect(rgbToHex([15, 15, 15])).toBe("#0f0f0f");
  });

  it("clamps values above 255", () => {
    expect(rgbToHex([300, 256, 999])).toBe("#ffffff");
  });

  it("clamps negative values to 0", () => {
    expect(rgbToHex([-1, -50, -100] as RGBTuple)).toBe("#000000");
  });

  it("returns black for undefined input", () => {
    expect(rgbToHex(undefined)).toBe("#000000");
  });

  it("returns black for invalid array length", () => {
    expect(rgbToHex([255, 128] as unknown as RGBTuple)).toBe("#000000");
    expect(rgbToHex([] as unknown as RGBTuple)).toBe("#000000");
  });
});

describe("parseColorInput", () => {
  describe("hex format with hash", () => {
    it("parses 6-digit hex with hash", () => {
      expect(parseColorInput("#ff5500")).toEqual([255, 85, 0]);
      expect(parseColorInput("#FF5500")).toEqual([255, 85, 0]);
      expect(parseColorInput("#000000")).toEqual([0, 0, 0]);
      expect(parseColorInput("#ffffff")).toEqual([255, 255, 255]);
      expect(parseColorInput("#FFFFFF")).toEqual([255, 255, 255]);
    });

    it("parses 3-digit shorthand hex with hash", () => {
      expect(parseColorInput("#f00")).toEqual([255, 0, 0]);
      expect(parseColorInput("#0f0")).toEqual([0, 255, 0]);
      expect(parseColorInput("#00f")).toEqual([0, 0, 255]);
      expect(parseColorInput("#F50")).toEqual([255, 85, 0]);
      expect(parseColorInput("#fff")).toEqual([255, 255, 255]);
      expect(parseColorInput("#FFF")).toEqual([255, 255, 255]);
    });
  });

  describe("hex format without hash", () => {
    it("parses 6-digit hex without hash", () => {
      expect(parseColorInput("ff5500")).toEqual([255, 85, 0]);
      expect(parseColorInput("FF5500")).toEqual([255, 85, 0]);
      expect(parseColorInput("000000")).toEqual([0, 0, 0]);
      expect(parseColorInput("ffffff")).toEqual([255, 255, 255]);
    });

    it("parses 3-digit shorthand hex without hash", () => {
      expect(parseColorInput("f00")).toEqual([255, 0, 0]);
      expect(parseColorInput("0f0")).toEqual([0, 255, 0]);
      expect(parseColorInput("00f")).toEqual([0, 0, 255]);
      expect(parseColorInput("F50")).toEqual([255, 85, 0]);
    });
  });

  describe("comma-separated RGB format", () => {
    it("parses comma-separated values without spaces", () => {
      expect(parseColorInput("255,128,0")).toEqual([255, 128, 0]);
      expect(parseColorInput("0,0,0")).toEqual([0, 0, 0]);
      expect(parseColorInput("255,255,255")).toEqual([255, 255, 255]);
    });

    it("parses comma-separated values with spaces", () => {
      expect(parseColorInput("255, 128, 0")).toEqual([255, 128, 0]);
      expect(parseColorInput("255,  128,  0")).toEqual([255, 128, 0]);
      expect(parseColorInput("0, 0, 0")).toEqual([0, 0, 0]);
    });

    it("clamps values above 255", () => {
      expect(parseColorInput("300,256,999")).toEqual([255, 255, 255]);
      expect(parseColorInput("256, 128, 0")).toEqual([255, 128, 0]);
    });
  });

  describe("rgb() function format", () => {
    it("parses rgb() format with spaces", () => {
      expect(parseColorInput("rgb(255, 128, 0)")).toEqual([255, 128, 0]);
      expect(parseColorInput("rgb(0, 0, 0)")).toEqual([0, 0, 0]);
      expect(parseColorInput("rgb(255, 255, 255)")).toEqual([255, 255, 255]);
    });

    it("parses rgb() format without spaces", () => {
      expect(parseColorInput("rgb(255,128,0)")).toEqual([255, 128, 0]);
    });

    it("parses RGB() with uppercase", () => {
      expect(parseColorInput("RGB(255, 128, 0)")).toEqual([255, 128, 0]);
      expect(parseColorInput("Rgb(255, 128, 0)")).toEqual([255, 128, 0]);
    });

    it("handles extra whitespace", () => {
      expect(parseColorInput("rgb( 255 , 128 , 0 )")).toEqual([255, 128, 0]);
    });

    it("clamps values above 255", () => {
      expect(parseColorInput("rgb(300, 256, 999)")).toEqual([255, 255, 255]);
    });
  });

  describe("edge cases and invalid input", () => {
    it("returns null for empty string", () => {
      expect(parseColorInput("")).toBeNull();
    });

    it("returns null for whitespace only", () => {
      expect(parseColorInput("   ")).toBeNull();
      expect(parseColorInput("\t")).toBeNull();
    });

    it("trims whitespace from valid input", () => {
      expect(parseColorInput("  #ff5500  ")).toEqual([255, 85, 0]);
      expect(parseColorInput("  255, 128, 0  ")).toEqual([255, 128, 0]);
    });

    it("returns null for invalid hex characters", () => {
      expect(parseColorInput("#gggggg")).toBeNull();
      expect(parseColorInput("#xyz123")).toBeNull();
    });

    it("returns null for invalid hex length", () => {
      expect(parseColorInput("#ff55")).toBeNull();
      expect(parseColorInput("#ff550")).toBeNull();
      expect(parseColorInput("#ff55001")).toBeNull();
    });

    it("returns null for incomplete RGB values", () => {
      expect(parseColorInput("255, 128")).toBeNull();
      // Note: "255" is valid as 3-digit hex (#225555)
    });

    it("interprets numeric-only 3-digit strings as hex", () => {
      // "255" is interpreted as hex #225555, not RGB
      expect(parseColorInput("255")).toEqual([34, 85, 85]);
      expect(parseColorInput("123")).toEqual([17, 34, 51]);
    });

    it("returns null for rgb() with wrong format", () => {
      expect(parseColorInput("rgb(255, 128)")).toBeNull();
      expect(parseColorInput("rgb(255)")).toBeNull();
      expect(parseColorInput("rgb()")).toBeNull();
    });

    it("returns null for random text", () => {
      expect(parseColorInput("red")).toBeNull();
      expect(parseColorInput("hello")).toBeNull();
      expect(parseColorInput("not a color")).toBeNull();
    });
  });
});

describe("roundtrip conversion", () => {
  it("converts RGB to hex and back", () => {
    const testCases: RGBTuple[] = [
      [255, 0, 0],
      [0, 255, 0],
      [0, 0, 255],
      [255, 128, 64],
      [128, 128, 128],
      [0, 0, 0],
      [255, 255, 255],
    ];

    for (const rgb of testCases) {
      const hex = rgbToHex(rgb);
      const parsed = parseColorInput(hex);
      expect(parsed).toEqual(rgb);
    }
  });
});
