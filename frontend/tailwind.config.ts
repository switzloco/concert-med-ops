import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontSize: {
        base: ["16px", "1.5"],
        sm: ["14px", "1.4"],
      },
      colors: {
        // Dark premium background colors
        medblack: {
          950: "#050508",
          900: "#0b0c10",
          800: "#15161e",
          700: "#1f212d",
          600: "#2a2c3a",
        },
        // Cyber / EDM neon colors
        cyber: {
          neonPink: "#ff007f",
          neonPurple: "#bc13fe",
          neonBlue: "#00f0ff",
          neonGreen: "#39ff14",
        },
        ocean: {
          950: "#050508",
          900: "#0b0c10",
          800: "#15161e",
          700: "#1f212d",
          600: "#2a2c3a",
          500: "#3b82f6",
          100: "#cbd5e1",
          50: "#f8fafc",
        },
        alert: {
          red: "#ef4444",
          amber: "#f59e0b",
          yellow: "#eab308",
          green: "#22c55e",
        },
      },
      boxShadow: {
        neonPurple: "0 0 10px rgba(188, 19, 254, 0.5), 0 0 20px rgba(188, 19, 254, 0.2)",
        neonBlue: "0 0 10px rgba(0, 240, 255, 0.5), 0 0 20px rgba(0, 240, 255, 0.2)",
        neonGreen: "0 0 10px rgba(57, 255, 20, 0.5), 0 0 20px rgba(57, 255, 20, 0.2)",
        neonPink: "0 0 10px rgba(255, 0, 127, 0.5), 0 0 20px rgba(255, 0, 127, 0.2)",
      },
    },
  },
  plugins: [],
};

export default config;
