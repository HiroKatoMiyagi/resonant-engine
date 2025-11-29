import '@testing-library/jest-dom';
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock environment variables
vi.stubGlobal('import.meta', {
  env: {
    VITE_WS_URL: 'ws://localhost:8000/ws/intents',
  },
});
