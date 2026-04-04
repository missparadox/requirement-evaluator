import { createBrowserRouter } from "react-router-dom";

import { UploadPage } from "../pages/UploadPage";


export const router = createBrowserRouter([
  { path: "/", element: <UploadPage /> },
]);
