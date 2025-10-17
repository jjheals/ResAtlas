// src/App.jsx
import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { MdLightMode, MdDarkMode } from "react-icons/md";
import { getTheme, toggleTheme } from './Theme';

import HomePage from "./pages/HomePage/HomePage";
import TableViewPage from './pages/TableView/TableView';

import './index.css';
import './App.css';


function App() {
    const [theme, setTheme] = useState(getTheme());

  /**
   * @const handleToggle
   * @abstract Event handler for when the user clicks the theme button.
   */
  const handleToggle = () => {
    toggleTheme();
    setTheme(getTheme());
  };

  // useEffect() => updates the [theme] state var when the user clicks the theme button.
  useEffect(() => {
    // update state when component mounts, in case theme was changed elsewhere
    setTheme(getTheme());
  }, []);


  return (
    <div className='app'>
      <BrowserRouter>
        <nav>
          <Link className='nav-link' to='/'>Home</Link>
          <Link className='nav-link' to='/table-view'>Table View</Link>
          <div className='nav-toggle-theme' onClick={handleToggle}>
            { theme == 'dark' ? <MdDarkMode className='theme-button' /> : <MdLightMode className='theme-button' />}
          </div>
        </nav>
        <Routes className='app-body-container' >
          <Route path='/' element={<HomePage />} />
          <Route path='/table-view' element={<TableViewPage />} />
        </Routes>
      </BrowserRouter>
    </div>
    
  );
}
export default App;
