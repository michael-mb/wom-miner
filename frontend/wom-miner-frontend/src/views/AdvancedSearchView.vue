<template>
    <div class="main-wrapper" id="main-wrapper">
        <Header/>
        <div class="page-wrapper">
            <div class="content container-fluid">
                <div class="page-header">
                    <div class="row">
                        <div class="col">
                            <h3 class="page-title">Advanced Search Page</h3>
                            <ul class="breadcrumb">
                                <li class="breadcrumb-item"><RouterLink to="/">Dashboard</RouterLink></li>
                                <li class="breadcrumb-item active">Search Page</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-sm-12">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="card-title">Customize your research</h5>
                                <p class="card-text">This page allows you to create <code>specialized queries</code> for what you are looking for. </p>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-sm">
                                        <div class="form-row row">
                                            <div class="col-md-6 mb-3">
                                                <label>Query</label>
                                                <div class="input-group">
                                                    <span class="input-group-text">Q</span>
                                                    <input v-model="keyword" type="text" class="form-control"  placeholder="Query" required>
                                                </div>
                                            </div>
                                            <div class="col-md-3 mb-3">
                                                <label>Response size [1-200]</label>
                                                <div class="input-group">
                                                    <span class="input-group-text">{{size}}</span>
                                                    <input v-model="size" type="range" min="1" max="200" class="form-control" required>
                                                </div>
                                            </div>
                                            <div class="col-md-3 mb-3">
                                                <label>Language</label>
                                                <div class="input-group">
                                                    <span class="input-group-text">{{lang.toUpperCase()}}</span>
                                                    <select v-model="lang" class="form-select">
                                                        <option value="de" selected>DE</option>
                                                        <option value="en">EN</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="form-row row">
                                            <div class="col-md-4 mb-4">
                                                <label>Entity Type</label>
                                                <div class="input-group">
                                                    <span class="input-group-text">T</span>
                                                    <select v-model="entityType" class="form-select">
                                                        <option value="research_project" selected>Reseach Projects</option>
                                                        <option value="org">Organizations</option>
                                                        <option value="people">People</option>
                                                    </select>
                                                </div>
                                            </div>
                                            <div class="col-md-3 mb-4">
                                                <label>University</label>
                                                <div class="input-group">
                                                    <span class="input-group-text">{{university.toUpperCase()}}</span>
                                                    <select v-model="university" class="form-select">
                                                        <option value="ude" selected>UDE</option>
                                                        <option value="rub">RUB</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                        <button class="btn btn-primary" @click="sendCustomRequest">
                                            <i class="fas fa-search" ></i>
                                            Search
                                            <span v-if="elastic.isSpinning" class="spinner-border spinner-border-sm me-2"></span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-12 d-flex">
                        <div class="card card-table">
                            <div class="card-header">
                                <h4 class="card-title">Results</h4>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-center table-hover datatable">
                                        <thead class="thead-light">
                                            <tr>
                                                <th>Type</th>
                                                <th>Title / Name</th>
                                                <th>Uni</th>
                                                <th>Last Update</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <template v-if="elastic.getCustomResult.length > 0">
                                                <tr style="cursor: pointer" @click="router.push(`/detail/${item._index}/${item._id}`)" v-for="item in elastic.getCustomResult">

                                                    <template v-if="globalUtils.extractTypeFromIndex(item._index) === 'research project'">
                                                        <td>{{globalUtils.capitalize(globalUtils.extractTypeFromIndex(item._index))}}</td>
                                                        <td>{{globalUtils.wrapTextInTable(item._source.title)}}</td>
                                                        <td>{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                        <td>{{globalUtils.formatDateTime(item._source.last_update)}}</td>
                                                    </template>
                                                    <template v-else-if="globalUtils.extractTypeFromIndex(item._index) === 'people'">
                                                        <td>{{globalUtils.capitalize(globalUtils.extractTypeFromIndex(item._index))}}</td>
                                                        <td>{{item._source.name}}</td>
                                                        <td>{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                        <td>-</td>
                                                    </template>
                                                    <template v-else-if="globalUtils.extractTypeFromIndex(item._index) === 'organization'">
                                                        <td>{{globalUtils.capitalize(item._source.type)}}</td>
                                                        <td>{{item._source.name}}</td>
                                                        <td>{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                        <td>-</td>
                                                    </template>
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
import {ref} from "vue";
import useElasticStore from "@/stores/elastic";
import globalUtils from "@/helpers/globalUtils";
import router from "@/router";

const elastic = useElasticStore()
const keyword = ref("")
const size = ref(1)
const lang = ref("de")
const entityType = ref("research_project")
const university = ref("ude")

function sendCustomRequest(){
    elastic.resetCustomResult()
    let request = {}
    if(entityType.value === "research_project"){
        request = {
            endpoint: `/${entityType.value}-${university.value}/_search`,
            query: {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "content": {
                                        "query": keyword.value.toLowerCase()
                                    }
                                }
                            },
                            {
                                "regexp": {
                                    "content": {
                                        "value": ".*" + keyword.value.toLowerCase() + ".*"
                                    }
                                }
                            }
                        ],
                        "must": [
                            {
                                "match": {
                                    "lang": {
                                        "query": lang.value
                                    }
                                }
                            },
                        ],
                    }
                },
                "size": size.value,
                "_source": ["title", "id", "type", "last_update", "url", "lang"],
                "sort": [
                    {
                        "_score": {
                            "order": "desc"
                        }
                    }
                ]
            }
        }
    }
    else if (entityType.value === "people"){
        request = {
            endpoint: `/${entityType.value}-${university.value}/_search`,
            query: {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "name": {
                                        "query": keyword.value.toLowerCase()
                                    }
                                }
                            },
                            {
                                "regexp": {
                                    "name": {
                                        "value": ".*" + keyword.value.toLowerCase() + ".*"
                                    }
                                }
                            }
                        ],
                    }
                },
                "size": size.value,
                "_source": ["name", "title", "email", "homepage.url", "in.url"],
                "sort": [
                    {
                        "_score": {
                            "order": "desc"
                        }
                    }
                ]
            }
        }
    }
    else if (entityType.value === "org"){
        request = {
            endpoint: `/${entityType.value}-${university.value}/_search`,
            query: {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "name": {
                                        "query": keyword.value.toLowerCase()
                                    }
                                }
                            },
                            {
                                "regexp": {
                                    "name": {
                                        "value": ".*" + keyword.value.toLowerCase() + ".*"
                                    }
                                }
                            }
                        ],
                    }
                },
                "size": size.value,
                "_source": ["link", "name", "uni", "upper", "type"],
                "sort": [
                    {
                        "_score": {
                            "order": "desc"
                        }
                    }
                ]
            }
        }
    }

    elastic.sendCustomRequest(request)
}
</script>

<style scoped>
th {
    cursor: pointer;
}
/***** Chrome, Safari, Opera, and Edge Chromium *****/
input[type="range"]::-webkit-slider-runnable-track {
    background: #e9ecef;
    border-radius: 20px;
}

/******** Firefox ********/
input[type="range"]::-moz-range-track {
    background: #e9ecef;
}

input[type=range]::-webkit-slider-thumb {
    -webkit-appearance: none;
    border: none;
    height: 15px;
    width: 15px;
    border-radius: 50%;
    background: #7638ff;
}

</style>