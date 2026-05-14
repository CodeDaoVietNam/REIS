import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface ErrorBoundaryState {
  error: Error | null;
}

export class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Dashboard runtime error:', error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <div className="mx-auto max-w-3xl px-6 py-24">
        <div className="glass-card border-error/40 p-8">
          <div className="mb-4 flex items-center gap-3 text-error">
            <AlertTriangle className="h-6 w-6" />
            <h1 className="text-2xl font-black">Frontend runtime error</h1>
          </div>
          <p className="mb-4 text-on-surface-variant">
            Trang không render được vì có lỗi runtime phía browser. Reload lại trang sau khi dev server được restart.
          </p>
          <pre className="overflow-auto rounded-2xl bg-surface-container-highest p-4 text-sm text-on-surface">
            {this.state.error.message}
          </pre>
        </div>
      </div>
    );
  }
}
