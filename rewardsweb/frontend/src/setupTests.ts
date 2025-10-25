import { TextEncoder, TextDecoder } from 'util';

// Add Node.js globals for browser environment
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as any;

// Mock fetch globally
global.fetch = jest.fn();

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: '',
  },
  writable: true,
});

// Mock btoa (base64 encoding)
global.btoa = (str: string) => Buffer.from(str, 'binary').toString('base64');

// Clear all mocks after each test
afterEach(() => {
  jest.clearAllMocks();
});