import { describe, expect, it } from 'vitest';

import { categoryLabel, statusLabel } from './utils';

describe('utils', () => {
  it('humanizes category labels', () => {
    expect(categoryLabel('digitization_incentive')).toBe('Digitization Incentive');
  });

  it('translates statuses', () => {
    expect(statusLabel('confirmed')).toBe('Confermato');
    expect(statusLabel('likely')).toBe('Probabile');
  });
});
