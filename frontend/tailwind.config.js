import frappeUIPreset from 'frappe-ui/tailwind'

const brand = {
  50: '#F5FAFF',
  100: '#E6F2FF',
  200: '#CCE5FF',
  300: '#B3D8FF',
  400: '#80BEFF',
  500: '#007CFF',
  600: '#0066CC',
  700: '#0052A3',
  800: '#004080',
  900: '#003366',
}

const brandAlias = {
  ...brand,
  950: brand[900],
}

export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    // INFO: uncomment the line below if you have workspaces set up
    // '../node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand,
        blue: brandAlias,
        amber: brandAlias,
        orange: brandAlias,
      },
      fontFamily: {
        sans: ['Montserrat', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        heading: ['Poppins', 'Montserrat', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
