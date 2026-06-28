import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // Merit brand palette
        merit: {
          gold: "#F4BA45",
          peach: "#FFECCF",
          cream: "#FAF7F2",
          sky: "#93D0EF",
        },
        gold: {
          50: "#FFFDF5",
          100: "#FFECCF",
          200: "#FFE0A8",
          300: "#F8D070",
          400: "#F4BA45",
          500: "#E5A830",
          600: "#C48B1E",
          700: "#9E6C14",
          800: "#7A5310",
          900: "#5C3D0B",
          950: "#3D2806",
        },
        sky: {
          50: "#F0F9FE",
          100: "#DBEFFE",
          200: "#BFE3FC",
          300: "#93D0EF",
          400: "#6BBBE8",
          500: "#4AA3DB",
          600: "#3585C0",
          700: "#2B6A9C",
          800: "#275681",
          900: "#24496B",
        },
        // shadcn/ui design tokens
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
      screens: {
        xs: "475px",
      },
    },
  },
  plugins: [require("@tailwindcss/forms")],
};

export default config;
