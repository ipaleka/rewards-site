// Create shared mock instances
const mockAtomicTransactionComposerInstances: Array<{
  addTransaction: jest.Mock;
  execute: jest.Mock;
}> = [];

export const AtomicTransactionComposer = jest.fn().mockImplementation(() => {
  const instance = {
    addTransaction: jest.fn(),
    execute: jest.fn().mockResolvedValue({
      confirmedRound: 1234,
      txIDs: ['test-tx-id']
    })
  };
  mockAtomicTransactionComposerInstances.push(instance);
  return instance;
});

// Helper to get the last created instance
export const getLastATCInstance = () => {
  return mockAtomicTransactionComposerInstances[mockAtomicTransactionComposerInstances.length - 1];
};

// Helper to clear all instances
export const clearATCInstances = () => {
  mockAtomicTransactionComposerInstances.length = 0;
};

export const makePaymentTxnWithSuggestedParamsFromObject = jest.fn().mockReturnValue({
  type: 'pay',
  from: 'test-address',
  to: 'test-address',
  amount: 0
});

export const encodeUnsignedTransaction = jest.fn().mockReturnValue(new Uint8Array([1, 2, 3]));

export const isValidAddress = jest.fn().mockReturnValue(true);