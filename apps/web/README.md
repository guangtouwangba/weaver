# Knowledge Platform Web

React frontend for the Knowledge Platform topic management system.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Ant Design** - UI component library
- **Axios** - HTTP client
- **Recharts** - Data visualization

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── api/          # API client modules
├── components/   # Reusable React components
├── pages/        # Page-level components
├── types/        # TypeScript type definitions
├── App.tsx       # Main app component
└── main.tsx      # Entry point
```

## Configuration

The dev server proxies API requests to `http://localhost:8000`.

Make sure the backend API server is running before starting the frontend.
