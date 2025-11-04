import { TextEncoder, TextDecoder } from "util";

// Add Node.js globals for browser environment
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as any;

// Mock fetch globally
global.fetch = jest.fn();

// Mock window.location
Object.defineProperty(window, "location", {
  value: {
    href: "",
  },
  writable: true,
});

// Mock btoa (base64 encoding)
global.btoa = (str: string) => Buffer.from(str, "binary").toString("base64");

// Mock algosdk
jest.mock("algosdk", () => {
  const originalAlgosdk = jest.requireActual("algosdk");
  return {
    ...originalAlgosdk,
    ABIContract: jest.fn(() => ({
      getMethodByName: jest.fn(() => ({ name: "mockMethod" })),
    })),
    AtomicTransactionComposer: jest.fn(() => ({
      addMethodCall: jest.fn(),
      execute: jest.fn().mockResolvedValue({
        confirmedRound: 123,
        txIDs: ["txid123"],
      }),
    })),
  };
});

// Clear all mocks after each test
afterEach(() => {
  jest.clearAllMocks();
});
