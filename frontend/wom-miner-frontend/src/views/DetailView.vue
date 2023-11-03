<template>
    <div class="main-wrapper" id="main-wrapper">
        <Header/>
        <div class="page-wrapper">
            <div class="content container-fluid">
                <div class="page-header" v-if="elastic.getSelectedDetailItem">
                    <div class="row">
                        <div class="col-sm-12">
                            <h3 class="page-title">Detail Page</h3>
                            <ul class="breadcrumb">
                                <li class="breadcrumb-item"><RouterLink to="/">Dashboard</RouterLink></li>
                                <li class="breadcrumb-item active">Detail Page /
                                    <template v-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) === 'organization'">
                                        {{globalUtils.capitalize(elastic.getSelectedDetailItem._source.type)}}
                                    </template>
                                    <template v-else>
                                        {{globalUtils.capitalize(globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index))}}
                                    </template>
                                    /
                                    <template v-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) === 'research project'">
                                        {{elastic.getSelectedDetailItem._source.title}}</template>
                                    <template v-else-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) === 'people'">
                                        {{`${elastic.getSelectedDetailItem._source.title}  ${elastic.getSelectedDetailItem._source.name}`}}</template>
                                    <template v-else-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) === 'organization'">
                                        {{elastic.getSelectedDetailItem._source.name}}</template>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>

                <template v-if="elastic.getSelectedDetailItem">
                    <div class="row">
                        <div class="col-12 d-flex">
                            <div class="card">
                                <div class="card-header">
                                    <h2 v-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) === 'research project'">
                                        {{elastic.getSelectedDetailItem._source.title}}</h2>
                                    <h2 v-else-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) === 'people'">
                                        {{`${elastic.getSelectedDetailItem._source.title}  ${elastic.getSelectedDetailItem._source.name}`}}</h2>
                                    <h2 v-else-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) === 'organization'">
                                        {{elastic.getSelectedDetailItem._source.name}}</h2>
                                </div>
                                <div class="card-body">
                                    <div class="table-responsive">
                                        <table class="table table-striped mb-0">
                                            <tbody>
                                                <template v-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) === 'organization'">
                                                    <tr>
                                                        <td>Type</td>
                                                        <td>{{globalUtils.capitalize(elastic.getSelectedDetailItem._source.type)}}</td>
                                                    </tr>
                                                    <tr v-if="elastic.getSelectedDetailItem._source['link']">
                                                        <td>Link</td>
                                                        <td>
                                                            <a target="_blank" :href="elastic.getSelectedDetailItem._source['link']">
                                                                {{elastic.getSelectedDetailItem._source['link']}}
                                                            </a>
                                                        </td>
                                                    </tr>
                                                </template>
                                                <tr v-else>
                                                    <td>Type</td>
                                                    <td>{{globalUtils.capitalize(globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index))}}</td>
                                                </tr>

                                                <template v-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) === 'research project'">
                                                    <tr>
                                                        <td>Last Update:</td>
                                                        <td>{{globalUtils.formatDateTime(elastic.getSelectedDetailItem._source.last_update)}}</td>
                                                    </tr>
                                                    <tr>
                                                        <td>Url</td>
                                                        <td><a target="_blank"
                                                               :href="elastic.getSelectedDetailItem._source.url">{{elastic.getSelectedDetailItem._source.url}}</a></td>
                                                    </tr>
                                                </template>

                                                <template v-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) === 'people'">
                                                    <tr v-if="elastic.getSelectedDetailItem._source.email">
                                                        <td>Email</td>
                                                        <td>
                                                            <a :href="`mailto:${elastic.getSelectedDetailItem._source.email}`">
                                                                {{elastic.getSelectedDetailItem._source.email}}
                                                            </a>
                                                        </td>
                                                    </tr>
                                                    <tr v-if="elastic.getSelectedDetailItem._source.homepages.length > 0">
                                                        <td>Homepages</td>
                                                        <td>
                                                            <template v-for="(link, index) in elastic.getSelectedDetailItem._source.homepages">
                                                                <a  target="_blank"
                                                                    :href="link">
                                                                    {{link}}
                                                                </a>
                                                                <span v-if="index !== keywords.length - 1 "></span>
                                                            </template>
                                                        </td>
                                                    </tr>
                                                    <tr v-if=" elastic.getSelectedDetailItem._source.found_in.length > 0">
                                                        <td>Found in</td>
                                                        <td>
                                                            <template v-for="(link, index) in elastic.getSelectedDetailItem._source.found_in">
                                                                <a  target="_blank"
                                                                    :href="link">
                                                                    {{link}}
                                                                </a>
                                                                <span v-if="index !== keywords.length - 1 "></span>
                                                            </template>
                                                        </td>
                                                    </tr>
                                                </template>

                                                <tr v-if="keywords.length > 0">
                                                    <td>Keywords</td>
                                                    <td>
                                                        <span v-for="(keyword,index) in keywords">
                                                            {{keyword}}<span v-if="index !== keywords.length - 1 ">, </span>
                                                        </span>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td>Favorite</td>
                                                    <td>
                                                        <button v-if="isFavorite" class="btn btn-primary ml-1 me-1" @click="removeToFavorite">
                                                            <i class="feather-trash-2"></i> Remove to Favorites
                                                        </button>
                                                        <button v-else class="btn btn-primary ml-1 me-1" @click="addToFavorite">
                                                            <i class="feather-star"></i> Add to Favorites
                                                        </button>
                                                    </td>
                                                </tr>
                                                <tr v-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) !== 'organization'">
                                                    <td>Graph Visualisation</td>
                                                    <td>
                                                        <RouterLink class="btn btn-primary ml-1 me-1 text-white"
                                                            :class="{ 'active': $route.name === 'graph' }" to="/graph_viz">
                                                            <i class="feather-share-2"></i> <span>Graph Visualization</span>
                                                        </RouterLink>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-6 d-flex"
                             v-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) === 'research project'">
                            <div class="card">
                                <div class="card-header">
                                    <h5 class="card-title">Text summary:</h5>
                                    <p>{{elastic.getSelectedDetailItem._source.summary}}</p>

                                    <h5 v-if="persons.length > 0" class="card-title">People:</h5>
                                    <p>
                                        <span v-for="(person,index) in persons">
                                            {{person}}<span v-if="index !== persons.length - 1 ">, </span> </span>
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div class="col-12 col-md-6 d-flex">
                            <div class="card card-table">
                                <div class="card-header">
                                    <h4 class="card-title"
                                        v-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) === 'organization'">Superior entities</h4>

                                    <h4 class="card-title"
                                        v-else>Probable related organizations</h4>
                                </div>
                                <div class="card-body">
                                    <div class="table-responsive">
                                        <table class="table table-center table-hover datatable mb-0">
                                            <thead class="thead-light">
                                            <tr>
                                                <th>Type</th>
                                                <th>Title/Name</th>
                                                <th>Uni</th>
                                            </tr>
                                            </thead>
                                            <tbody>
                                                <tr v-if="globalUtils.extractUniFromIndex(elastic.getSelectedDetailItem._index) === 'RUB'" style="cursor: pointer">
                                                    <td @click="relocate('https://www.ruhr-uni-bochum.de/de')">University</td>
                                                    <td @click="relocate('https://www.ruhr-uni-bochum.de/de')">Ruhr Universität Bochum</td>
                                                    <td @click="relocate('https://www.ruhr-uni-bochum.de/de')">RUB</td>
                                                </tr>
                                                <tr v-else style="cursor: pointer">
                                                    <td @click="relocate('https://www.uni-due.de/')">University</td>
                                                    <td @click="relocate('https://www.uni-due.de/')">Universität Duisburg Essen</td>
                                                    <td @click="relocate('https://www.uni-due.de/')">UDE</td>
                                                </tr>
                                                <tr style="cursor: pointer"  v-for="item in globalUtils.extractTopXByType(elastic.getRelatedEntities, 'organization', 7)">
                                                    <template v-if="(item._id !== elastic.getSelectedDetailItem._id)">
                                                        <td @click="navigateAndReload(item)">{{globalUtils.capitalize(item._source.type)}}</td>
                                                        <td @click="navigateAndReload(item)">{{item._source.name}}</td>
                                                        <td @click="navigateAndReload(item)">{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                    </template>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-12 col-md-6 d-flex" v-if="elastic.getSelectedDetailItem && elastic.getRelatedEntities.length > 0">
                            <div v-if="globalUtils.extractTypeFromIndex(elastic.getSelectedDetailItem._index) !== 'organization'" class="card card-table">
                                <div class="card-header">
                                    <h4 class="card-title">Probable related entities</h4>
                                </div>
                                <div class="card-body">
                                    <div class="table-responsive">
                                        <table class="table table-center table-hover datatable">
                                            <thead class="thead-light">
                                            <tr>
                                                <th>Type</th>
                                                <th>Title/Name</th>
                                                <th>Uni</th>
                                            </tr>
                                            </thead>
                                            <tbody>
                                                <tr style="cursor: pointer" v-for="item in toShowRelatedEntities('research project')">
                                                    <template v-if="(item._id !== elastic.getSelectedDetailItem._id)">
                                                        <td @click="navigateAndReload(item)">{{globalUtils.capitalize(globalUtils.extractTypeFromIndex(item._index))}}</td>
                                                        <td @click="navigateAndReload(item)">{{globalUtils.wrapTextInTable(item._source.title)}}</td>
                                                        <td @click="navigateAndReload(item)">{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                    </template>
                                                </tr>
                                                <tr style="cursor: pointer"  v-for="item in toShowRelatedEntities('people')">
                                                    <template v-if="(item._id !== elastic.getSelectedDetailItem._id)">
                                                        <td @click="navigateAndReload(item)">{{globalUtils.capitalize(globalUtils.extractTypeFromIndex(item._index))}}</td>
                                                        <td @click="navigateAndReload(item)">{{item._source.name}}</td>
                                                        <td @click="navigateAndReload(item)">{{globalUtils.extractUniFromIndex(item._index)}}</td>
                                                    </template>
                                                </tr>
                                            </tbody>
                                            <template v-if="elastic.getRelatedEntities">
                                                <div v-if="relatedMore === false && (globalUtils.extractTopXByType(elastic.getRelatedEntities, 'research project', -1).length +
                                            globalUtils.extractTopXByType(elastic.getRelatedEntities,'people', -1).length) > 5" class="see-more" title="see more"
                                                     @click="relatedMore = true">
                                                    <i class="fa fa-plus-circle"></i>
                                                </div>

                                                <div v-if="relatedMore === true" class="see-more" title="see more"
                                                     @click="relatedMore = false">
                                                    <i class="fa fa-minus-circle"></i>
                                                </div>
                                            </template>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </template>
            </div>
        </div>
    </div>
</template>

<script setup>
import Header from "@/components/Header.vue";
import {useRoute} from "vue-router";
import useElasticStore from "@/stores/elastic";
import globalUtils from "@/helpers/globalUtils";
import {ref} from "vue";
import {BASE} from "@/config/config";

const route = useRoute()
const elastic = useElasticStore()
const id = route.params.id
const index = route.params.index

const favorites = ref([])
favorites.value = JSON.parse(localStorage.getItem("favorites"))

const isFavorite = ref(false)
const persons = ref([])
const keywords = ref([])
const relatedMore = ref(false)

function toShowRelatedEntities(type){
    let numberOfEntities = -1
    if(!relatedMore.value)
        numberOfEntities = 5
    return globalUtils.extractTopXByType(elastic.getRelatedEntities, type, numberOfEntities)
}
async function findDocument(){
    const request = `/${index}/_doc/${id}`
    elastic.findDocument(request).then(async () => {
        // Get Related Entities
        elastic.resetRelatedEntities()
        const selectedItem = await elastic.getSelectedDetailItem
        isFavorite.value = elastic.isFavorite(selectedItem)
        let toSearch = ""
        let url = ""
        let request
        if(selectedItem._source.doc)
            keywords.value = selectedItem._source.doc.keywords.slice(0,6)

        if (globalUtils.extractTypeFromIndex(selectedItem._index) === "research project") {
            // Connect Projects with Persons
            let person_names = globalUtils.extractPersons(selectedItem._source.person_names).slice(0, 10)
            persons.value = person_names

            for (const name of person_names) {
                request = {
                    endpoint: `/people-${globalUtils.extractUniFromIndex(selectedItem._index).toLowerCase()}/_search`,
                    query: {
                        "query": {
                            "bool": {
                                "should": [
                                    {
                                        "match": {
                                            "name": {
                                                "query": name.toLowerCase(),
                                                boost: 10
                                            }
                                        }
                                    },
                                ],
                            }
                        },
                        "size": 15,
                        "min_score": 100,
                        "_source": ["name", "title", "email", "found_in", "homepages"],
                        "sort": [
                            {
                                "_score": {
                                    "order": "desc"
                                }
                            }
                        ]
                    }
                }
                await elastic.fetchRelatedEntities(request)
            }

            // Connect Projects with Orgs
            url = selectedItem._source["url"]
            request = {
                endpoint: `/org-${globalUtils.extractUniFromIndex(selectedItem._index).toLowerCase()}/_search`,
                query: {
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "match": {
                                        "link": {
                                            "query": url
                                        }
                                    }
                                },
                            ],
                        }
                    },
                    "size": 10,
                    "min_score": 5,
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
            await elastic.fetchRelatedEntities(request)
        }
        else if (globalUtils.extractTypeFromIndex(selectedItem._index) === "people") {
            toSearch = selectedItem._source.name

            // Connect People with Projects
            request = {
                endpoint: `/research_project-${globalUtils.extractUniFromIndex(selectedItem._index).toLowerCase()}/_search`,
                query: {
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "match": {
                                        "content": {
                                            "query": toSearch.toLowerCase()
                                        }
                                    }
                                },
                            ],
                        }
                    },
                    "size": 30,
                    "min_score": 4,
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
            await elastic.fetchRelatedEntities(request)

            // Connect People with ORG
            const urls = [...selectedItem._source.homepages, ...selectedItem._source.found_in]
            for (const url of urls) {
                request = {
                    endpoint: `/org-${globalUtils.extractUniFromIndex(selectedItem._index).toLowerCase()}/_search`,
                    query: {
                        "query": {
                            "bool": {
                                "should": [
                                    {
                                        "match": {
                                            "link": {
                                                "query": url
                                            }
                                        }
                                    },
                                ],
                            }
                        },
                        "size": 10,
                        "min_score": 5.5,
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
                await elastic.fetchRelatedEntities(request)
            }
        }
        else if (globalUtils.extractTypeFromIndex(selectedItem._index) === "organization") {
            // GET UPPER
            if(selectedItem._source.type === "faculty")
                return
            if(selectedItem._source.type === "institute" || selectedItem._source.type === "chair" ){
                if(!selectedItem._source.upper)
                    return

                request = {
                    endpoint: `/org-${globalUtils.extractUniFromIndex(selectedItem._index).toLowerCase()}/_search`,
                    query: {
                        "query": {
                            "bool": {
                                "should": [
                                    {
                                        "match": {
                                            "name": {
                                                "query": selectedItem._source.upper
                                            }
                                        }
                                    },
                                ],
                            }
                        },
                        "size": 1,
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
                await elastic.fetchRelatedEntities(request)
            }
        }
    }).finally(() => {
        elastic.createNodes(elastic.getSelectedDetailItem, elastic.getRelatedEntities)
    })
}
findDocument()

function addToFavorite(){
    elastic.addFavorite(elastic.getSelectedDetailItem)
    isFavorite.value = true
}

function removeToFavorite(){
    elastic.removeFavorite(elastic.getSelectedDetailItem)
    isFavorite.value = false
}

function navigateAndReload(item) {
    window.location = BASE +`/detail/${item._index}/${item._id}`
}

function relocate(link){
    window.location = link
}
</script>

<style scoped>
th {
    cursor: pointer;
}

.see-more {
    position: absolute;
    left: 50%;
    bottom: -23px;
    transform: translateX(-50%);
    font-size: 30px;
    color: #7638ff;
    cursor: pointer;
}
</style>