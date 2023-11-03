<template>
    <div class="main-wrapper" id="main-wrapper">
        <Header/>
        <div class="page-wrapper">
            <div class="content container-fluid">

                <div class="page-header">
                    <div class="row">
                        <div class="col-sm-12">
                            <h3 class="page-title">Explore Page</h3>
                            <ul class="breadcrumb">
                                <li class="breadcrumb-item"><RouterLink to="/">Dashboard</RouterLink></li>
                                <li class="breadcrumb-item active">Explore Page</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-sm-12">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="card-title">Customize Graph View</h5>
                                <p class="card-text">This page allows you to explore <code>the documents</code> based on a starting search point.
                                    The legend to understand the graph is provided below.</p>

                                <p class="card-text">
                                    <span><code>R -</code> Research Project </span>
                                    <span class="m-3"><code>P -</code> People </span>
                                    <span class="m-3"><code>F -</code> Faculty</span>
                                    <span class="m-3"><code>I -</code> Institute</span>
                                    <span class="m-3"><code>C -</code> Chair</span>
                                </p>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-sm">
                                        <div class="form-row row">
                                            <div class="col-md-6 mb-3">
                                                <h5 class="card-title">Orientation</h5>
                                                <div class="input-group">
                                                    <div class="radio mt-2">
                                                        <input value="0" type="radio" name="0" v-model="treeOrientation"> Vertical
                                                    </div>
                                                    <div class="radio ml-2 mt-2">
                                                        <input value="1" type="radio" name="radio" v-model="treeOrientation"> Horizontal
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row mb-5 super-row">
                    <div class="col-12 d-flex" style="position:relative;overflow: scroll;" v-if="elastic.getGraph">
                        <blocks-tree  :data="elastic.getGraph" :class="elastic.isSpinning ? 'black-overlay' : ''"
                                      :horizontal="treeOrientation==='1'"  :collapsable="true">
                            <template #node="{data,context}" >
                                <div style="position: relative">
                                    <span v-if="elastic.isSpinning && currentNodeId === data.some_id" class="spinner-border spinner-border-sm me-2 super-pos"></span>
                                    <a :href="data.link" target="_blank"><i class="feather-external-link external" ></i></a>
                                    <div style="cursor:pointer;" @click="fetchChildren(data.index, data.some_id)">
                                        <span><code>{{data.type}}</code></span><br>
                                        <span>
                                            {{globalUtils.wrapTextInTable(data.label)}}
                                        </span>
                                    </div>
                                </div>
                            </template>
                        </blocks-tree>
                    </div>
                    <div class="col-12 d-flex" v-else>
                        <div class="card">
                            <div class="card-header">
                                <p class="card-text">You must <code>first search for a documents</code> before viewing...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>


</template>

<script setup>
import {ref} from "vue"
import Header from "@/components/Header.vue";
import useElasticStore from "@/stores/elastic";
import globalUtils from "../helpers/globalUtils";

const elastic = useElasticStore()
let selected = ref([]);
let treeOrientation = ref("0");
const currentNodeId = ref(undefined)


const toggleSelect = (node, isSelected) => {
    isSelected ? selected.value.push(node.some_id) : selected.value.splice(selected.value.indexOf(node.some_id), 1);
    if(node.children && node.children.length) {
        node.children.forEach(ch=>{
            toggleSelect(ch,isSelected)
        })
    }
}

function fetchChildren(index, id){
    elastic.resetRelatedNodes()
    currentNodeId.value = id
    const request = `/${index}/_doc/${id}`
    elastic.fetchChildNodes(request).then( async () => {
        const fetchedNode = elastic.getFetchedNode
        let toSearch = ""
        let url = ""
        let request
        if (globalUtils.extractTypeFromIndex(fetchedNode._index) === "research project") {
            let person_names = globalUtils.extractPersons(fetchedNode._source.person_names).slice(0, 10)
            // Connect Projects with Persons
            for (const name of person_names) {
                request = {
                    endpoint: `/people-${globalUtils.extractUniFromIndex(fetchedNode._index).toLowerCase()}/_search`,
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
                        "min_score": 100,
                        "size": 5,
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
                await elastic.fetchRelatedNodes(request)
            }

            // Connect Projects with Orgs
            url = fetchedNode._source["url"]
            request = {
                endpoint: `/org-${globalUtils.extractUniFromIndex(fetchedNode._index).toLowerCase()}/_search`,
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
                    "min_score": 4,
                    "size": 7,
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
            await elastic.fetchRelatedNodes(request)
        }
        else if (globalUtils.extractTypeFromIndex(fetchedNode._index) === "people") {

            toSearch = fetchedNode._source.name
            // Connect People with Projects
            request = {
                endpoint: `/research_project-${globalUtils.extractUniFromIndex(fetchedNode._index).toLowerCase()}/_search`,
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
                    "min_score": 4,
                    "size": 4,
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
            await elastic.fetchRelatedNodes(request)

            // Connect People with ORG
            const urls = [...fetchedNode._source.homepages, ...fetchedNode._source.found_in]
            for (const url of urls) {
                request = {
                    endpoint: `/org-${globalUtils.extractUniFromIndex(fetchedNode._index).toLowerCase()}/_search`,
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
                        "min_score": 5,
                        "size": 4,
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
                await elastic.fetchRelatedNodes(request)
            }
        }
        else if (globalUtils.extractTypeFromIndex(fetchedNode._index) === "organization") {
            //GET UPPER
            if(fetchedNode._source.type === "faculty")
                return
            if(fetchedNode._source.type === "institute" || fetchedNode._source.type === "chair" ){
                if(!fetchedNode._source.upper)
                    return

                request = {
                    endpoint: `/org-${globalUtils.extractUniFromIndex(fetchedNode._index).toLowerCase()}/_search`,
                    query: {
                        "query": {
                            "bool": {
                                "should": [
                                    {
                                        "match": {
                                            "name": {
                                                "query": fetchedNode._source.upper
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
                await elastic.fetchRelatedNodes(request)
            }
        }
    }).finally(() => {
        let related = []
        globalUtils.extractTopXByType(elastic.getRelatedNodes, "people", 5).forEach(item => {
            related.push(elastic.createChildNode(item))
        })
        globalUtils.extractTopXByType(elastic.getRelatedNodes, "research project", 5).forEach(item => {
            related.push(elastic.createChildNode(item))
        })
        globalUtils.extractTopXByType(elastic.getRelatedNodes, "organization", 5).forEach(item => {
            related.push(elastic.createChildNode(item))
        })
        elastic.addChildNode(elastic.getGraph, elastic.getFetchedNode._id, related)
    })
}

</script>
<style scoped>
.super-pos{
    color: #d63384;
    position: absolute;
    top: 1px;
    left: 1px;
}
.external {
    position: absolute;
    right: 10px;
}
.ml-2{
    margin-left: 15px !important;
}

.mt-2{
    margin-top: 15px !important;
}
</style>

