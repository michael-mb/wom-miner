<template>
    <div class="main-wrapper" id="main-wrapper">
        <Header/>
        <div class="page-wrapper">
            <div class="content container-fluid">

                <div class="page-header">
                    <div class="row">
                        <div class="col">
                            <h3 class="page-title">Favorites Page</h3>
                            <ul class="breadcrumb">
                                <li class="breadcrumb-item"><RouterLink to="/">Dashboard</RouterLink></li>
                                <li class="breadcrumb-item active">Favorites Page</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-12 d-flex">
                        <div class="card card-table">
                            <div class="card-header">
                                <h4 class="card-title">Favorites items</h4>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-center table-hover datatable">
                                        <thead class="thead-light">
                                            <tr>
                                                <th>Type</th>
                                                <th>Title / Name</th>
                                                <th>Uni</th>
                                                <th></th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr v-for="item in favorites" style="cursor: pointer">
                                                <template v-if="globalUtils.extractTypeFromIndex(item._index) === 'research project'">
                                                    <td @click="router.push(`/detail/${item._index}/${item._id}`)">
                                                        {{globalUtils.extractTypeFromIndex(item._index)}}</td>
                                                    <td @click="router.push(`/detail/${item._index}/${item._id}`)">
                                                        {{globalUtils.wrapTextInTable(item._source.title)}}</td>
                                                    <td @click="router.push(`/detail/${item._index}/${item._id}`)">
                                                        {{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                    <td>
                                                        <button class="btn btn-primary ml-1 me-1" @click="removeToFavorite(item)">
                                                            <i class="feather-trash-2"></i> Remove
                                                        </button>
                                                    </td>
                                                </template>
                                                <template v-if="globalUtils.extractTypeFromIndex(item._index) === 'people'">
                                                    <td @click="router.push(`/detail/${item._index}/${item._id}`)">
                                                        {{globalUtils.extractTypeFromIndex(item._index)}}</td>
                                                    <td @click="router.push(`/detail/${item._index}/${item._id}`)">
                                                        {{item._source.name}}</td>
                                                    <td @click="router.push(`/detail/${item._index}/${item._id}`)">
                                                        {{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                    <td>
                                                        <button class="btn btn-primary ml-1 me-1" @click="removeToFavorite(item)">
                                                            <i class="feather-trash-2"></i> Remove
                                                        </button>
                                                    </td>
                                                </template>
                                                <template v-if="globalUtils.extractTypeFromIndex(item._index) === 'organization'">
                                                    <td @click="router.push(`/detail/${item._index}/${item._id}`)">
                                                        {{globalUtils.capitalize(item._source.type)}}</td>
                                                    <td @click="router.push(`/detail/${item._index}/${item._id}`)">
                                                        {{item._source.name}}</td>
                                                    <td @click="router.push(`/detail/${item._index}/${item._id}`)">
                                                        {{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                    <td>
                                                        <button class="btn btn-primary ml-1 me-1" @click="removeToFavorite(item)">
                                                            <i class="feather-trash-2"></i> Remove
                                                        </button>
                                                    </td>
                                                </template>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>


</template>

<script setup>
import Header from "@/components/Header.vue";
import useElasticStore from "@/stores/elastic";
import globalUtils from "@/helpers/globalUtils";
import {ref} from "vue";
import router from "@/router";

const elastic = useElasticStore()

const favorites = ref([])
favorites.value = JSON.parse(localStorage.getItem("favorites"))

function removeToFavorite(item){
    elastic.removeFavorite(item)
    favorites.value = JSON.parse(localStorage.getItem("favorites"))
}
</script>

<style scoped>
th {
    cursor: pointer;
}
</style>