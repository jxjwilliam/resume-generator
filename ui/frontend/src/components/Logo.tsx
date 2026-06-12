import { Box, Typography } from "@mui/material";

export default function Logo() {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, flexGrow: 1 }}>
      <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="logoGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#fff" stop-opacity="0.15"/>
            <stop offset="100%" stop-color="#fff" stop-opacity="0.05"/>
          </linearGradient>
        </defs>
        {/* Document body */}
        <path d="M5 3h15l7 7v19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"
              fill="url(#logoGrad)" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/>
        {/* Page fold */}
        <path d="M20 3v7h7" fill="none" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"
              opacity="0.4"/>
        {/* Text lines */}
        <rect x="8" y="13" width="13" height="1.5" rx="0.75" fill="#fff" opacity="0.7"/>
        <rect x="8" y="17" width="15" height="1.5" rx="0.75" fill="#fff" opacity="0.7"/>
        <rect x="8" y="21" width="11" height="1.5" rx="0.75" fill="#fff" opacity="0.5"/>
        <rect x="8" y="25" width="8" height="1.5" rx="0.75" fill="#fff" opacity="0.35"/>
        {/* Sparkle / AI magic */}
        <path d="M24 7.5l.6-1.1.6 1.1 1.1.6-1.1.6-.6 1.1-.6-1.1-1.1-.6z"
              fill="#f5a623"/>
      </svg>
      <Typography variant="h6" sx={{ fontWeight: 700, letterSpacing: "-0.02em" }}>
        Resume Forge
      </Typography>
    </Box>
  );
}
