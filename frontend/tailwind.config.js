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
        /* Cloud Dancer = фон. Кнопки/линии: #303F20 + PANTONE 14-1036 TPG (#D9AE5F). */
        coffee: {
          50: '#F0EEE9',
          100: '#E5D2B8',
          200: '#DDD5C8',
          300: '#D2AB80',
          400: '#490900',
          500: '#490900',
          600: '#490900',
          700: '#D9AE5F', // PANTONE 14-1036 TPG (Ochre)
          800: '#303F20', // основной цвет кнопок/линий
          900: '#490900', // основной текст под логотип
          950: '#1f2a14', // hover/active для тёмно-зелёных кнопок
        },
      },
      fontFamily: {
        /* Rafchik в файлах часто без кириллицы — не ставим его в sans/display, иначе «?» вместо русских букв. */
        display: ['Georgia', 'Cambria', 'Times New Roman', 'serif'],
        sans: ['system-ui', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        /* Только латиница/цифры в макетах; кириллица уйдёт на Georgia по цепочке */
        raf: ['Rafchik', 'Georgia', 'Cambria', 'serif'],
      },
    },
  },
  plugins: [],
};
