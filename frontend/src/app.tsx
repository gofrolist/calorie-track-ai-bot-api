import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Today } from './pages/today';
import { MealDetail } from './pages/meal-detail';
import { Stats } from './pages/stats';
import { Goals } from './pages/goals';

const router = createBrowserRouter([
  { path: '/', element: <Today /> },
  { path: '/meal/:id', element: <MealDetail /> },
  { path: '/stats', element: <Stats /> },
  { path: '/goals', element: <Goals /> },
]);

const App: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default App;
