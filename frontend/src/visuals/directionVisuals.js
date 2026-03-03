import heroAiStudio from '../assets/hero-ai-studio.png'
import directionIcons from '../assets/directions-icons.png'

// Simple mapping for direction-specific visuals.
// generatedUrl can be hydrated later from backend/model output.
export const directionVisuals = {
  code: {
    key: 'code',
    placeholderUrl: heroAiStudio,
    generatedUrl: null,
    prompt:
      'Dark futuristic AI build studio interface, focus on full-stack code editor and API panel, glassmorphism, deep navy background with blue-violet accents.',
  },
  video: {
    key: 'video',
    placeholderUrl: heroAiStudio,
    generatedUrl: null,
    prompt:
      'AI video generation workspace with timeline, storyboard frames, and preview player, neon purple and teal on dark background.',
  },
  audio: {
    key: 'audio',
    placeholderUrl: heroAiStudio,
    generatedUrl: null,
    prompt:
      'AI audio and podcast studio with waveforms, tracks, and mixing console, cyan and violet glows on dark UI.',
  },
  slides: {
    key: 'slides',
    placeholderUrl: heroAiStudio,
    generatedUrl: null,
    prompt:
      'Slide deck generator interface with slide thumbnails, outline panel, and theme controls, dark futuristic presentation tool.',
  },
  pdf: {
    key: 'pdf',
    placeholderUrl: heroAiStudio,
    generatedUrl: null,
    prompt:
      'Technical PDF report builder with sections, charts, and document preview, refined dark theme with subtle grid.',
  },
}

export const directionIconStrip = directionIcons

export function resolveDirectionImage(directionKey) {
  const entry = directionVisuals[directionKey]
  if (!entry) return null
  return entry.generatedUrl || entry.placeholderUrl
}

