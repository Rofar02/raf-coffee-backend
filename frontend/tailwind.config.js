/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './menu.html', './admin.html'],
  theme: {
    extend: {
      colors: {
        /* Бренд-референс (шкала STUDIO FLEUR с картинки): MATCHA, ALMOND, PISTACHE, CHAI, CAROB, VANILLA */
        brand: {
          matcha: '#809671',
          almond: '#E5E0D8',
          pistache: '#B3B792',
          chai: '#D2AB80',
          carob: '#725C3A',
          vanilla: '#E5D2B8',
        },
        /* Та же гамма в шкале coffee-* — чтобы не переписывать все классы */
        coffee: {
          50: '#E5E0D8',
          100: '#E5D2B8',
          200: '#DDD5C8',
          300: '#D2AB80',
          400: '#C3B589',
          500: '#B3B792',
          600: '#9BA081',
          700: '#809671',
          800: '#725C3A',
          900: '#5a4830',
        },
      },
      fontFamily: {
        /* Совпадает с @font-face в src/rafchik-fonts.css */
        display: ['Rafchik', 'Georgia', 'Cambria', 'Times New Roman', 'serif'],
        sans: ['Rafchik', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
