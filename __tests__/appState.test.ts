import {
  appReducer,
  initialState,
  computeEffectiveScore,
  looksLikeSmiles,
  resolveCompoundPreset,
  type AppState,
  type AppAction,
} from '@/lib/appState';

describe('appReducer', () => {
  it('should return initial state', () => {
    const state = appReducer(initialState, { type: 'SET_PAGE', page: 'input' });
    expect(state.currentPage).toBe('input');
  });

  it('should handle SET_PAGE action', () => {
    const state = appReducer(initialState, { type: 'SET_PAGE', page: 'results' });
    expect(state.currentPage).toBe('results');
  });

  it('should handle SET_INPUT action', () => {
    const state = appReducer(initialState, { type: 'SET_INPUT', value: 'Aspirin' });
    expect(state.inputValue).toBe('Aspirin');
  });

  it('should handle SET_DOSE action', () => {
    const state = appReducer(initialState, { type: 'SET_DOSE', dose: 2.5 });
    expect(state.dose).toBe(2.5);
  });

  it('should handle SELECT_PRESET action', () => {
    const state = appReducer(initialState, { type: 'SELECT_PRESET', name: 'Ibuprofen' });
    expect(state.selectedPreset).toBe('Ibuprofen');
    expect(state.selectedDrugLabel).toBe('Ibuprofen');
    expect(state.inputValue).toBe('Ibuprofen');
    expect(state.dose).toBe(1.0);
    expect(state.errorMessage).toBeNull();
  });

  it('should handle SET_API_STATUS action', () => {
    const state = appReducer(initialState, { type: 'SET_API_STATUS', online: true });
    expect(state.apiOnline).toBe(true);
  });

  it('should handle START_ANALYSIS action', () => {
    const state = appReducer(initialState, { type: 'START_ANALYSIS' });
    expect(state.isAnalyzing).toBe(true);
    expect(state.errorMessage).toBeNull();
    expect(state.currentPage).toBe('results');
  });

  it('should handle ANALYSIS_ERROR action', () => {
    const state = appReducer(
      { ...initialState, isAnalyzing: true },
      { type: 'ANALYSIS_ERROR', message: 'Connection failed' }
    );
    expect(state.isAnalyzing).toBe(false);
    expect(state.errorMessage).toBe('Connection failed');
    expect(state.currentPage).toBe('input');
  });

  it('should handle CLEAR_ERROR action', () => {
    const stateWithError = { ...initialState, errorMessage: 'Some error' };
    const state = appReducer(stateWithError, { type: 'CLEAR_ERROR' });
    expect(state.errorMessage).toBeNull();
  });
});

describe('computeEffectiveScore', () => {
  const mockDrug = {
    name: 'Test Drug',
    smiles: 'CC',
    score: 80,
    verdict: 'SAFE',
    verdictColor: 'green',
    trialReady: true,
    trialTitle: 'Ready',
    trialDesc: 'Test',
    trialColor: 'green',
    trialIcon: 'check',
    trialBg: 'green',
    pk: { absorption: 1, clearance: 1, vd: 1, halflife: 1, bio: 80, protein: 50 },
    pkBars: { absorption: 50, clearance: 50, vd: 50, halflife: 50, bio: 80, protein: 50 },
    pkColors: { absorption: 'green', clearance: 'green', vd: 'green', halflife: 'green', bio: 'green', protein: 'green' },
    risks: [],
    flags: [],
    flagTypes: [],
    badgeTxt: 'Safe',
    badgeType: 'safe' as const,
    pathway: [],
    organDetail: { brain: '', lungs: '', heart: '', liver: '', kidneys: '' },
  };

  it('should return 0 when drug is null', () => {
    expect(computeEffectiveScore(null, 1)).toBe(0);
  });

  it('should return drug score at dose 1.0', () => {
    expect(computeEffectiveScore(mockDrug, 1.0)).toBe(80);
  });

  it('should reduce score at higher doses', () => {
    const scoreAt1 = computeEffectiveScore(mockDrug, 1.0);
    const scoreAt3 = computeEffectiveScore(mockDrug, 3.0);
    expect(scoreAt3).toBeLessThan(scoreAt1);
  });
});

describe('looksLikeSmiles', () => {
  it('should detect SMILES with special characters', () => {
    expect(looksLikeSmiles('CC(=O)Nc1ccc(O)cc1')).toBe(true);
    expect(looksLikeSmiles('C#N')).toBe(true);
    expect(looksLikeSmiles('[Na+]')).toBe(true);
  });

  it('should not detect regular drug names as SMILES', () => {
    expect(looksLikeSmiles('tylenol')).toBe(false);
    expect(looksLikeSmiles('ibuprofen')).toBe(false);
  });
});

describe('resolveCompoundPreset', () => {
  const lookup = {
    'Tylenol': { id: '1', name: 'Tylenol', smiles: 'CC(=O)Nc1ccc(O)cc1', aliases: ['acetaminophen', 'paracetamol'] },
    'Aspirin': { id: '2', name: 'Aspirin', smiles: 'CC(=O)OC1=CC=CC=C1C(=O)O' },
  };

  it('should find exact match', () => {
    const result = resolveCompoundPreset('Tylenol', lookup);
    expect(result?.name).toBe('Tylenol');
  });

  it('should find case-insensitive match', () => {
    const result = resolveCompoundPreset('tylenol', lookup);
    expect(result?.name).toBe('Tylenol');
  });

  it('should find by alias', () => {
    const result = resolveCompoundPreset('acetaminophen', lookup);
    expect(result?.name).toBe('Tylenol');
  });

  it('should return undefined for unknown compound', () => {
    const result = resolveCompoundPreset('Unknown Drug', lookup);
    expect(result).toBeUndefined();
  });
});
