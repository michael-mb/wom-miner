<template>
  <div class="header header-one">
    <div class="header-left header-left-one">
        <router-link to="/" class="remove-link-attr"><p style="font-size: 22px;" class="wom-title"><i class="fab fa-wpexplorer fs-30"></i> UNI - Explorer</p></router-link>
    </div>
    <a href="javascript:void(0);" id="toggle_btn">
      <i class="fas fa-bars"></i>
    </a>
    <a class="mobile_btn" id="mobile_btn">
      <i class="fas fa-bars"></i>
    </a>
  </div>
  <div class="sidebar" id="sidebar">
    <div class="sidebar-inner slimscroll"  >
      <div id="sidebar-menu" class="sidebar-menu">
        <ul>
          <li>
              <RouterLink :class="{ 'active': $route.name === 'home' }" to="/"><i class="feather-home"></i> <span>Home</span></RouterLink>
          </li>
          <li>
              <RouterLink :class="{ 'active': $route.name === 'search' }"  to="/search"><i class="feather-search"></i> <span>Global Search</span></RouterLink>
          </li>
          <li>
              <RouterLink :class="{ 'active': $route.name === 'advanced_search' }"  to="/advanced_search"><i class="feather-zoom-in"></i> <span>Advanced Search</span></RouterLink>
          </li>
          <li>
              <RouterLink :class="{ 'active': $route.name === 'favorites' }" to="/favorites"><i class="feather-star"></i> <span>Favorites</span></RouterLink>
          </li>
          <li>
              <RouterLink :class="{ 'active': $route.name === 'about' }" to="/about"><i class="feather-info"></i> <span>About</span></RouterLink>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style>
.header-left {
    width: 230px !important;
}

.remove-link-attr{
    color: #455560;
}

@media only screen and (max-width: 991px) {
    .wom-title {
        margin-left: 20px;
    }
    .header-left {
        width: 280px !important;
    }
}

.sidebar-overlay {
    background-color: unset;
}
</style>
