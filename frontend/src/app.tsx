import { lazy } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TelegramProvider } from '@/providers/telegram';
import { AppLayout } from '@/components/layout/AppLayout';

const Meals = lazy(() => import('@/pages/meals'));
const Stats = lazy(() => import('@/pages/stats'));
const Goals = lazy(() => import('@/pages/goals'));
const Feedback = lazy(() => import('@/pages/feedback'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <Meals /> },
      { path: '/stats', element: <Stats /> },
      { path: '/goals', element: <Goals /> },
      { path: '/feedback', element: <Feedback /> },
    ],
  },
]);

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TelegramProvider>
        <RouterProvider router={router} />
      </TelegramProvider>
    </QueryClientProvider>
  );
}
