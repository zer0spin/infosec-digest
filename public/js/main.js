document.addEventListener('DOMContentLoaded', () => {
  const content = document.getElementById('content');
  const sidebar = document.getElementById('sidebar');
  const tooltip = document.getElementById('tooltip');
  let ALL_DATA = {};
  let tooltipTimeout;

  const timeAgo = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    if (isNaN(date)) return '';
    const now = new Date();
    const seconds = Math.round((now - date) / 1000);
    const minutes = Math.round(seconds / 60);
    const hours = Math.round(minutes / 60);
    const days = Math.round(hours / 24);
    if (days > 365) return `${Math.round(days / 365.25)}y ago`;
    if (days > 30) return `${Math.round(days / 30.44)}mo ago`;
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return `${seconds}s ago`;
  };

  const preventXSS = (str) => {
    if (typeof str !== 'string') return '';
    const p = document.createElement('p'); p.textContent = str; return p.innerHTML;
  };

  function isValidItem(item) {
    return item && typeof item === 'object' && 
           typeof item.title === 'string' && 
           typeof item.link === 'string';
  }

  const renderReddit = (category) => {
    const redditItems = [];
    Object.values(ALL_DATA.news || {}).forEach(items => {
      items.forEach(item => {
        if (!isValidItem(item)) return; 
        if (item.type === 'reddit' && item.category === category) {
          redditItems.push(item);
        }
      });
    });

    if (redditItems.length === 0) { content.innerHTML = '<h2>No Reddit posts found.</h2>'; return; }
    let title = category;
    if (category === 'br') { title = '🇧🇷 Brazil Reddit'; } 
    else if (category === 'jobs') { title = 'Security Jobs'; }
    let html = `<h2>${preventXSS(title)}</h2>`;
    redditItems.sort((a, b) => new Date(b.published) - new Date(a.published));
    redditItems.forEach(item => {
      const timeTag = item.published ? `<span class="time-ago">${timeAgo(item.published)}</span>` : '';
      const sourceTag = `<span class="source-tag" style="background-color:${preventXSS(item.color)}">${preventXSS(item.source_name)}</span>`;
      html += `<article class="content-item"><div class="item-header">${timeTag}${sourceTag}<a href="${preventXSS(item.link)}" target="_blank" rel="noopener noreferrer" class="item-title" data-summary="${preventXSS(item.summary)}" data-link="${preventXSS(item.link)}">${preventXSS(item.title)}</a></div></article>`;
    });
    content.innerHTML = html;
  };

  const renderNews = (category) => {
    if (!ALL_DATA.news || !ALL_DATA.news[category]) { content.innerHTML = '<h2>No news found.</h2>'; return; }
    const newsItems = ALL_DATA.news[category].filter(item => {
        return isValidItem(item) && item.type !== 'reddit';
    });
    if (newsItems.length === 0) { content.innerHTML = '<h2>No news found.</h2>'; return; }
    let categoryTitle = preventXSS(category);
    if (category === 'Brazil') { categoryTitle = `🇧🇷 ${categoryTitle}`; }
    let html = `<h2>${categoryTitle}</h2>`;
    newsItems.forEach(item => {
      const timeTag = item.published ? `<span class="time-ago">${timeAgo(item.published)}</span>` : '';
      const sourceTag = `<span class="source-tag" style="background-color:${preventXSS(item.color)}">${preventXSS(item.source_name)}</span>`;
      html += `<article class="content-item"><div class="item-header">${timeTag}${sourceTag}<a href="${preventXSS(item.link)}" target="_blank" rel="noopener noreferrer" class="item-title" data-summary="${preventXSS(item.summary)}" data-link="${preventXSS(item.link)}">${preventXSS(item.title)}</a></div></article>`;
    });
    content.innerHTML = html;
  };

  const renderPodcasts = (showName) => {
    if (!ALL_DATA.podcasts || !ALL_DATA.podcasts[showName]) { content.innerHTML = '<h2>No episodes found.</h2>'; return; }
    let html = `<h2>${preventXSS(showName)}</h2>`;
    ALL_DATA.podcasts[showName].forEach(episode => {
      if (!isValidItem(episode)) return; // Valida antes de processar
      const timeTag = episode.published ? `<span class="time-ago">${timeAgo(episode.published)}</span>` : '';
      html += `<article class="content-item"><div class="item-header">${timeTag}<a href="${preventXSS(episode.link)}" target="_blank" rel="noopener noreferrer" class="item-title" data-summary="${preventXSS(episode.summary)}" data-link="${preventXSS(episode.link)}">${preventXSS(episode.title)}</a></div></article>`;
    });
    content.innerHTML = html;
  };

  const buildSidebar = () => {
    let sidebarHtml = '';
    const redditCategories = {};
    Object.values(ALL_DATA.news || {}).flat().forEach(item => {
        if(isValidItem(item) && item.type === 'reddit' && item.category){
            if(!redditCategories[item.category]) redditCategories[item.category] = 0;
            redditCategories[item.category]++;
        }
    });

    if (Object.keys(redditCategories).length > 0) {
      sidebarHtml += '<h2>Reddit</h2><ul class="nav">';
      for(const category in redditCategories){
        sidebarHtml += `<li><a href="#" data-type="reddit" data-category="${preventXSS(category)}">${preventXSS(category)} (${redditCategories[category]})</a></li>`;
      }
      sidebarHtml += '</ul>';
    }
    
    const newsCategories = {};
    Object.keys(ALL_DATA.news || {}).sort().forEach(category => {
        const count = ALL_DATA.news[category].filter(item => isValidItem(item) && item.type !== 'reddit').length;
        if(count > 0) newsCategories[category] = count;
    });

    if (Object.keys(newsCategories).length > 0) {
      sidebarHtml += '<h2>News</h2><ul class="nav">';
      for(const category in newsCategories){
        let displayCategory = category;
        if (category === 'Brazil') { displayCategory = `🇧🇷 ${category}`; }
        sidebarHtml += `<li><a href="#" data-type="news" data-category="${preventXSS(category)}">${displayCategory}</a></li>`;
      }
      sidebarHtml += '</ul>';
    }

    const podcastShows = Object.keys(ALL_DATA.podcasts || {}).sort();
    if (podcastShows.length > 0) {
      sidebarHtml += '<h2>Podcasts</h2><ul class="nav">';
      podcastShows.forEach(showName => {
        const validEpisodes = ALL_DATA.podcasts[showName].filter(isValidItem);
        if (validEpisodes.length > 0) {
          sidebarHtml += `<li><a href="#" data-type="podcast" data-category="${preventXSS(showName)}">${preventXSS(showName)} (${validEpisodes.length})</a></li>`;
        }
      });
      sidebarHtml += '</ul>';
    }
    sidebar.innerHTML = sidebarHtml || '<p>No content found.</p>';
  };
  
  const setActiveLink = (clickedLink) => {
    document.querySelectorAll('#sidebar a').forEach(link => link.classList.remove('active'));
    if (clickedLink) { clickedLink.classList.add('active'); }
  };

  sidebar.addEventListener('click', (e) => {
    e.preventDefault();
    const target = e.target;
    if (target.tagName === 'A') {
      const type = target.dataset.type;
      const category = target.dataset.category;
      setActiveLink(target);
      if (type === 'news') { renderNews(category); } 
      else if (type === 'reddit') { renderReddit(category); }
      else if (type === 'podcast') { renderPodcasts(category); }
    }
  });

  content.addEventListener('mouseover', (e) => { if (e.target.matches('.item-title')) { const targetLink = e.target; tooltipTimeout = setTimeout(() => { const summary = targetLink.dataset.summary; const link = targetLink.dataset.link; if (summary) { tooltip.innerHTML = `<p>${summary}</p><a href="${link}" target="_blank" rel="noopener noreferrer">Read full story &rarr;</a>`; tooltip.style.display = 'block'; } }, 500); } });
  content.addEventListener('mouseout', (e) => { if (e.target.matches('.item-title')) { clearTimeout(tooltipTimeout); tooltip.style.display = 'none'; } });
  content.addEventListener('mousemove', (e) => { if (tooltip.style.display === 'block') { tooltip.style.left = e.pageX + 15 + 'px'; tooltip.style.top = e.pageY + 15 + 'px'; } });

  fetch('data.json')
    .then(response => { if (!response.ok) { throw new Error(`HTTP error! status: ${response.status}`); } return response.json(); })
    .then(data => {
      if(!data || typeof data !== 'object'){
        throw new Error("data.json is not a valid object.");
      }
      const sortItems = (items) => {
        if(!Array.isArray(items)) return;
        items.sort((a, b) => { const dateA = new Date(a.published); const dateB = new Date(b.published); if (isNaN(dateA)) return 1; if (isNaN(dateB)) return -1; return dateB - dateA; });
      };
      
      for (const category in data.news) { sortItems(data.news[category]); }
      for (const show in data.podcasts) { sortItems(data.podcasts[show]); }
      ALL_DATA = data;
      buildSidebar();
      const firstNewsCategory = Object.keys(ALL_DATA.news || {}).sort().find(cat => ALL_DATA.news[cat].some(item => item.type !== 'reddit'));
      if (firstNewsCategory) {
        renderNews(firstNewsCategory);
        setActiveLink(sidebar.querySelector(`a[data-type="news"]`));
      } else { content.innerHTML = '<p>No content available. Please run the fetcher and check logs.</p>'; }
    })
    .catch(error => {
      console.error('Failed to load data:', error);
      sidebar.innerHTML = '';
      content.innerHTML = '<h2>Error</h2><p>Could not load `data.json`. Please run the fetcher script and check the `fetcher.log` for errors.</p>';
    });
});