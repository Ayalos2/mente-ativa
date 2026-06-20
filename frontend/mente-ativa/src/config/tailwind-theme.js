// Configuração customizada do Tailwind CSS
import { theme, typography, transitions } from './theme.js'

export default {
  theme: {
    extend: {
      colors: {
        primary: theme.colors.primary,
        slate: theme.colors.slate,
      },
      fontFamily: typography.fontFamily,
      fontSize: typography.fontSize,
      fontWeight: typography.fontWeight,
      spacing: theme.spacing,
      borderRadius: theme.borderRadius,
      boxShadow: theme.shadows,
      transitionDuration: transitions.duration,
      transitionTimingFunction: transitions.easing,
      zIndex: theme.zIndex,
    },
  },
  plugins: [],
}