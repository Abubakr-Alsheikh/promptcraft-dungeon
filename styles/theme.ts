import {
  extendTheme,
  StyleFunctionProps,
  type ThemeConfig,
} from "@chakra-ui/react";

// Define color palette (adjust these to fit the desired dungeon aesthetic)
const colors = {
  brand: {
    primary: "#8B4513", // SaddleBrown - earthy, solid
    secondary: "#A0522D", // Sienna - warmer earth tone
    accent: "#FFD700", // Gold - for treasure, highlights
    textDark: "#2F4F4F", // DarkSlateGray - readable text
    textLight: "#F5F5DC", // Beige - for dark backgrounds
    bgDark: "#1A202C", // Gray.800 - deep background
    bgLight: "#F7FAFC", // Gray.50 - lighter sections
    danger: "#E53E3E", // Red.500 - for errors, low health
    success: "#48BB78", // Green.400 - for success, positive feedback
    info: "#4299E1", // Blue.400 - for hints, info
  },
  // Add more semantic colors if needed (e.g., monster, item rarity)
  rarity: {
    common: "#A0AEC0", // Gray.400
    uncommon: "#48BB78", // Green.400
    rare: "#4299E1", // Blue.400
    epic: "#9F7AEA", // Purple.400
    legendary: "#ED8936", // Orange.400
  },
};

// Configure initial color mode and usage
const config: ThemeConfig = {
  initialColorMode: "dark",
  useSystemColorMode: false,
};

// Extend the default theme
const theme = extendTheme({
  config,
  colors,
  fonts: {
    heading: `'MedievalSharp', serif`,
    body: `'Lato', sans-serif`,
  },
  // Add component style overrides if needed later
  components: {
    Button: {
      baseStyle: {
        fontWeight: "bold",
      },
      variants: {
        solid: (props: StyleFunctionProps) => ({
          bg: props.colorMode === "dark" ? "brand.primary" : "brand.secondary",
          color: "white",
          _hover: {
            bg:
              props.colorMode === "dark" ? "brand.secondary" : "brand.primary",
          },
        }),
      },
    },
  },
  styles: {
    global: (props: StyleFunctionProps) => ({
      body: {
        bg: props.colorMode === "dark" ? "brand.bgDark" : "brand.bgLight",
        color:
          props.colorMode === "dark" ? "brand.textLight" : "brand.textDark",
        transitionProperty: "background-color",
        transitionDuration: "normal",
        lineHeight: "base",
      },
      // Example: Style scrollbars for a more integrated look
      "::-webkit-scrollbar": {
        width: "8px",
        height: "8px",
      },
      "::-webkit-scrollbar-track": {
        background: props.colorMode === "dark" ? "gray.700" : "gray.200",
      },
      "::-webkit-scrollbar-thumb": {
        background:
          props.colorMode === "dark" ? "brand.primary" : "brand.secondary",
        borderRadius: "4px",
        "&:hover": {
          background:
            props.colorMode === "dark" ? "brand.secondary" : "brand.primary",
        },
      },
    }),
  },
});

export default theme;
