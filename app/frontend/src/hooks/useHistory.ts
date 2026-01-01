import { useState, useCallback, useMemo } from 'react';

interface HistoryState<T> {
    past: T[];
    present: T;
    future: T[];
}

export interface HistoryActions<T> {
    state: T;
    set: (newPresent: T | ((prev: T) => T)) => void;
    undo: () => void;
    redo: () => void;
    canUndo: boolean;
    canRedo: boolean;
    reset: (initialState: T) => void;
}

export function useHistory<T>(initialState: T, maxHistory = 50): HistoryActions<T> {
    const [history, setHistory] = useState<HistoryState<T>>({
        past: [],
        present: initialState,
        future: [],
    });

    const canUndo = history.past.length > 0;
    const canRedo = history.future.length > 0;

    const undo = useCallback(() => {
        setHistory((prev) => {
            if (prev.past.length === 0) return prev;

            const previous = prev.past[prev.past.length - 1];
            const newPast = prev.past.slice(0, prev.past.length - 1);

            return {
                past: newPast,
                present: previous,
                future: [prev.present, ...prev.future],
            };
        });
    }, []);

    const redo = useCallback(() => {
        setHistory((prev) => {
            if (prev.future.length === 0) return prev;

            const next = prev.future[0];
            const newFuture = prev.future.slice(1);

            return {
                past: [...prev.past, prev.present],
                present: next,
                future: newFuture,
            };
        });
    }, []);

    const set = useCallback((value: T | ((prev: T) => T)) => {
        setHistory((prev) => {
            const newPresent = value instanceof Function ? value(prev.present) : value;

            if (prev.present === newPresent) return prev;

            const newPast = [...prev.past, prev.present];
            if (newPast.length > maxHistory) {
                newPast.shift();
            }

            return {
                past: newPast,
                present: newPresent,
                future: [], // Clear future on new action
            };
        });
    }, [maxHistory]);

    const reset = useCallback((initialState: T) => {
        setHistory({
            past: [],
            present: initialState,
            future: [],
        });
    }, []);

    return useMemo(() => ({
        state: history.present,
        set,
        undo,
        redo,
        canUndo,
        canRedo,
        reset
    }), [history.present, undo, redo, canUndo, canRedo, set, reset]);
}
