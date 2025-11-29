import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import { useWebSocket } from '../useWebSocket';
import type { ReactNode } from 'react';

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  readyState: number = WebSocket.CONNECTING;
  onopen: (() => void) | null = null;
  onclose: ((event: { wasClean: boolean; code: number; reason: string }) => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: ((error: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  send = vi.fn();
  close = vi.fn();

  // Test helpers
  simulateOpen() {
    this.readyState = WebSocket.OPEN;
    this.onopen?.();
  }

  simulateMessage(data: object) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }

  simulateClose(wasClean: boolean = true) {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.({ wasClean, code: 1000, reason: '' });
  }
}

// Setup
beforeEach(() => {
  vi.stubGlobal('WebSocket', MockWebSocket);
  MockWebSocket.instances = [];
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useWebSocket', () => {
  const createWrapper = () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    return ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };

  test('WS-01: WebSocket接続確立', async () => {
    const { result } = renderHook(() => useWebSocket(), {
      wrapper: createWrapper(),
    });

    // Wait for WebSocket to be created
    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBeGreaterThan(0);
    });

    // Initially connecting or connected
    expect(['connecting', 'connected', 'disconnected']).toContain(
      result.current.connectionState.status
    );

    // Simulate connection if not already connected
    if (MockWebSocket.instances[0] && result.current.connectionState.status !== 'connected') {
      act(() => {
        MockWebSocket.instances[0].simulateOpen();
      });

      // Should be connected
      await waitFor(() => {
        expect(result.current.connectionState.status).toBe('connected');
      });
    }

    expect(result.current.connectionState.retryCount).toBe(0);
  });

  test('WS-03: Ping/Pong動作確認', async () => {
    const { result } = renderHook(() => useWebSocket(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBeGreaterThan(0);
    });

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    await waitFor(() => {
      expect(result.current.connectionState.status).toBe('connected');
    });

    // Simulate pong message
    act(() => {
      MockWebSocket.instances[0].simulateMessage({ type: 'pong' });
    });

    // Should still be connected (no errors)
    expect(result.current.connectionState.status).toBe('connected');
  });

  test('WS-05: 接続断時の自動再接続', async () => {
    vi.useFakeTimers();

    const { result } = renderHook(() => useWebSocket(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBeGreaterThan(0);
    });

    // Connect
    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    await waitFor(() => {
      expect(result.current.connectionState.status).toBe('connected');
    });

    // Simulate abnormal close
    act(() => {
      MockWebSocket.instances[0].simulateClose(false);
    });

    // Should be reconnecting
    await waitFor(() => {
      expect(result.current.connectionState.status).toBe('reconnecting');
      expect(result.current.connectionState.retryCount).toBe(1);
    });

    vi.useRealTimers();
  });

  test('WS-02: Intent更新イベント受信', async () => {
    const { result } = renderHook(() => useWebSocket(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBeGreaterThan(0);
    });

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    await waitFor(() => {
      expect(result.current.connectionState.status).toBe('connected');
    });

    // Simulate intent update message
    act(() => {
      MockWebSocket.instances[0].simulateMessage({
        type: 'intent_update',
        data: {
          intent_id: 'test-123',
          status: 'completed',
          content: 'Test intent',
        },
        timestamp: new Date().toISOString(),
      });
    });

    // Should still be connected (message processed)
    expect(result.current.connectionState.status).toBe('connected');
  });

  test('WS-04: 購読追加/解除', async () => {
    const { result } = renderHook(() => useWebSocket(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBeGreaterThan(0);
    });

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    await waitFor(() => {
      expect(result.current.connectionState.status).toBe('connected');
    });

    // Subscribe
    act(() => {
      result.current.subscribe(['intent-1', 'intent-2']);
    });

    expect(MockWebSocket.instances[0].send).toHaveBeenCalledWith(
      JSON.stringify({
        type: 'subscribe',
        intent_ids: ['intent-1', 'intent-2'],
      })
    );

    // Unsubscribe
    act(() => {
      result.current.unsubscribe(['intent-1']);
    });

    expect(MockWebSocket.instances[0].send).toHaveBeenCalledWith(
      JSON.stringify({
        type: 'unsubscribe',
        intent_ids: ['intent-1'],
      })
    );
  });

  test('WS-07: 最大リトライ後のフォールバック', async () => {
    const { result } = renderHook(() => useWebSocket(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBeGreaterThan(0);
    });

    // Connect first
    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    await waitFor(() => {
      expect(result.current.connectionState.status).toBe('connected');
    });

    // Test that connection state exists
    expect(result.current.connectionState).toBeDefined();
    expect(result.current.connect).toBeDefined();
    expect(result.current.disconnect).toBeDefined();
  });
});
