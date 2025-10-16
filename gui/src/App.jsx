// src/App.jsx
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';


import HomePage from "./pages/HomePage/HomePage";
import TableViewPage from './pages/TableView/TableView';

function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to='/'>Home</Link>
        <Link to='/table-view'>Table View</Link>
      </nav>
      <Routes>
        <Route path='/' element={<HomePage />} />
        <Route path='/table-view' element={<TableViewPage />} />
      </Routes>
    </BrowserRouter>
  );
}
export default App;
