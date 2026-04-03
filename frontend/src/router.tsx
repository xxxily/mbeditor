import { createBrowserRouter } from "react-router-dom";
import { lazy, Suspense } from "react";
import MainLayout from "./components/layout/MainLayout";

const Editor = lazy(() => import("./pages/Editor"));
const ArticleList = lazy(() => import("./pages/ArticleList"));
const Settings = lazy(() => import("./pages/Settings"));

function LazyPage({ children }: { children: React.ReactNode }) {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center h-full">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      {children}
    </Suspense>
  );
}

const router = createBrowserRouter([
  {
    path: "/",
    element: <MainLayout />,
    children: [
      { index: true, element: <LazyPage><ArticleList /></LazyPage> },
      { path: "editor/:id", element: <LazyPage><Editor /></LazyPage> },
      { path: "settings", element: <LazyPage><Settings /></LazyPage> },
    ],
  },
]);

export default router;
