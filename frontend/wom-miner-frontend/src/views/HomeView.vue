<template>
    <div class="main-wrapper" id="main-wrapper">
        <Header/>
        <div class="page-wrapper">
            <div class="content container-fluid">

                <div class="page-header">
                    <div class="row">
                        <div class="col-sm-12">
                            <h3 class="page-title">Home Page</h3>
                            <ul class="breadcrumb">
                                <li class="breadcrumb-item"><RouterLink to="/">Dashboard</RouterLink></li>
                                <li class="breadcrumb-item active">Home Page</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div class="row">

                    <div class="col-12 col-md-8 d-flex">
                        <div class="card card-table">
                            <div class="card-header">
                                <h4 class="card-title">Recently viewed</h4>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-center table-hover datatable">
                                        <thead class="thead-light">
                                        <tr>
                                            <th>Type</th>
                                            <th>Title</th>
                                            <th>Uni</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        <template v-if="recentlyViewed">
                                            <tr v-for="item in recentlyViewed"
                                                style="cursor:pointer;"
                                                @click="router.push(`/detail/${item._index}/${item._id}`)">
                                                <template v-if="globalUtils.extractTypeFromIndex(item._index) === 'research project'">
                                                    <td>{{globalUtils.extractTypeFromIndex(item._index)}}</td>
                                                    <td>{{globalUtils.wrapTextInTable(item._source.title)}}</td>
                                                    <td>{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                </template>
                                                <template v-if="globalUtils.extractTypeFromIndex(item._index) === 'people'">
                                                    <td>{{globalUtils.extractTypeFromIndex(item._index)}}</td>
                                                    <td>{{item._source.name}}</td>
                                                    <td>{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                </template>
                                                <template v-if="globalUtils.extractTypeFromIndex(item._index) === 'organization'">
                                                    <td>{{globalUtils.capitalize(item._source.type)}}</td>
                                                    <td>{{item._source.name}}</td>
                                                    <td>{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                </template>
                                            </tr>
                                        </template>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-12 col-md-4 d-flex">
                        <div class="card card-table">
                            <div class="card-header">
                                <h4 class="card-title">Researchers of the day</h4>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-center table-hover datatable">
                                        <thead class="thead-light">
                                        <tr>
                                            <th>Name</th>
                                            <th>Uni</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        <tr v-for="item in elastic.getPersonsOfTheDay"
                                            @click="router.push(`/detail/${item._index}/${item._id}`)"
                                            style="cursor: pointer">
                                            <td>{{item._source.name}}</td>
                                            <td>{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                        </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="col-12 col-md-4 d-flex" v-if="elastic.getStats">
                        <div class="card card-table">
                            <div class="card-header">
                                <h4 class="card-title">Some statistics</h4>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-center datatable">
                                        <thead class="thead-light">
                                            <tr>
                                                <th>Name</th>
                                                <th>Value</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr v-if="elastic.getStats['project-ude']">
                                                <td>Number of UDE Projects mined</td>
                                                <td>{{elastic.getStats['project-ude'].value}} projects</td>
                                            </tr>
                                            <tr v-if="elastic.getStats['project-rub']">
                                                <td>Number of RUB Projects mined</td>
                                                <td>{{elastic.getStats['project-rub'].value}} projects</td>
                                            </tr>
                                            <tr v-if="elastic.getStats['people-ude']">
                                                <td>Number of UDE People mined</td>
                                                <td>{{elastic.getStats['people-ude'].value}} people</td>
                                            </tr>
                                            <tr v-if="elastic.getStats['people-rub']">
                                                <td>Number of RUB People mined</td>
                                                <td>{{elastic.getStats['people-rub'].value}} people</td>
                                            </tr>
                                            <tr v-if="elastic.getStats['org-ude']">
                                                <td>Number of UDE organizations mined</td>
                                                <td>{{elastic.getStats['org-ude'].value}} organizations</td>
                                            </tr>
                                            <tr v-if="elastic.getStats['org-rub']">
                                                <td>Number of RUB organizations mined</td>
                                                <td>{{elastic.getStats['org-rub'].value}} organizations</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-12 col-md-8 d-flex">
                        <div class="card card-table">
                            <div class="card-header">
                                <h4 class="card-title">Latest projects added</h4>
                            </div>

                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-center table-hover datatable">
                                        <thead class="thead-light">
                                        <tr>
                                            <th>Title</th>
                                            <th>Uni</th>
                                            <th>Last Update</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                            <template v-if="elastic.getLatestProjects.length > 0">
                                                <tr v-for="item in globalUtils.sortByLastUpdate(elastic.getLatestProjects)"
                                                    @click="router.push(`/detail/${item._index}/${item._id}`)"
                                                    style="cursor: pointer">
                                                    <td>{{globalUtils.wrapTextInTable(item._source.title)}}</td>
                                                    <td>{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                    <td>{{globalUtils.formatDateTime(item._source.last_update)}}</td>
                                                </tr>
                                            </template>
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
import {ref} from "vue";
import globalUtils from "@/helpers/globalUtils";
import router from "@/router";

const elastic = useElasticStore()

const recentlyViewed = ref(undefined)
recentlyViewed.value = JSON.parse(localStorage.getItem("recently_viewed"))

function getLatestProjects(){
    elastic.resetStats()
    elastic.resetLatestProjects()
    elastic.resetPersonsOfTheDay()

    elastic.fetchLatestProjects("/research_project-ude/_search")
    elastic.fetchLatestProjects("/research_project-rub/_search")

    let request = {
        endpoint: "/research_project-ude/_search",
        org: "project-ude",
        query: {
            query: {
                "match_all": {}
            },
            size: 0,
            track_total_hits: true
        }
    }
    elastic.fetchStatistics(request)

    request = {
        endpoint: "/research_project-rub/_search",
        org: "project-rub",
        query: {
            query: {
                "match_all": {}
            },
            size: 0,
            track_total_hits: true
        }
    }
    elastic.fetchStatistics(request)

    request = {
        endpoint: "/people-ude/_search",
        org: "people-ude",
        query: {
            query: {
                "match_all": {}
            },
            size: 0,
            track_total_hits: true
        }
    }
    elastic.fetchStatistics(request)

    request = {
        endpoint: "/people-rub/_search",
        org: "people-rub",
        query: {
            query: {
                "match_all": {}
            },
            size: 0,
            track_total_hits: true
        }
    }
    elastic.fetchStatistics(request)

    request = {
        endpoint: "/org-ude/_search",
        org: "org-ude",
        query: {
            query: {
                "match_all": {}
            },
            size: 0,
            track_total_hits: true
        }
    }
    elastic.fetchStatistics(request)

    request = {
        endpoint: "/org-rub/_search",
        org: "org-rub",
        query: {
            query: {
                "match_all": {}
            },
            size: 0,
            track_total_hits: true
        }
    }
    elastic.fetchStatistics(request)
}

getLatestProjects()

function getPersonOfTheDay(){
    elastic.fetchPersonsOfTheDay("/people-ude/_search")
    elastic.fetchPersonsOfTheDay("/people-rub/_search")
}
getPersonOfTheDay()
</script>