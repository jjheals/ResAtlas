// src/Theme.js

const THEME_KEY = "ui.theme"; // 'light' | 'dark' | 'auto'
const root = document.documentElement;
const media = window.matchMedia("(prefers-color-scheme: dark)");


function applyThemeMode(mode) {
  // Remove manual override by default
  root.removeAttribute("data-theme");

  if (mode === "light") root.setAttribute("data-theme", "light");
  else if (mode === "dark") root.setAttribute("data-theme", "dark");
  // else 'auto' -> no attribute; CSS @media handles it
}


export function setTheme(mode /* 'light' | 'dark' | 'auto' */) {
  localStorage.setItem(THEME_KEY, mode);
  applyThemeMode(mode);
}


export function getTheme() {
  return localStorage.getItem(THEME_KEY) || "auto";
}


export function initTheme() {
  // 1) apply saved choice
  applyThemeMode(getTheme());

  // 2) react if OS theme changes while in 'auto'
  media.addEventListener("change", () => {
    if (getTheme() === "auto") applyThemeMode("auto");
  });
}



// Optional: helper to toggle light<->dark quickly
export function toggleTheme() {
  const cur = getTheme();
  const next = cur === "dark" ? "light" : "dark";
  setTheme(next);
}
